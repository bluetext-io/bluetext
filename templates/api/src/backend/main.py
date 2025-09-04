import uvicorn
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from .utils import log
from .routes import router
from . import conf

log.init(conf.get_log_level())
logger = log.get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database connection if enabled
    if conf.USE_POSTGRES:
        from .db import init_db, init_connection, close_db
        await init_db()
        await init_connection()
    
    # Initialize Couchbase client if enabled
    if conf.USE_COUCHBASE:
        from .clients.couchbase import CouchbaseClient
        couchbase_config = conf.get_couchbase_conf()
        app.state.couchbase_client = CouchbaseClient(couchbase_config)
        await app.state.couchbase_client.initialize()
        await app.state.couchbase_client.init_connection()

    yield

    # Clean up database connection if enabled
    if conf.USE_POSTGRES:
        await close_db()
    
    # Clean up Couchbase client if enabled
    if conf.USE_COUCHBASE:
        await app.state.couchbase_client.close()

app = FastAPI(
    title="Backend API",
    version="0.1.0",
    docs_url="/docs",
    lifespan=lifespan
)

app.include_router(router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def main() -> None:
    if not conf.validate():
        raise ValueError("Invalid configuration.")

    http_conf = conf.get_http_conf()
    logger.info(f"Starting API on port {http_conf.port}")
    uvicorn.run(
        "backend.main:app",
        host=http_conf.host,
        port=http_conf.port,
        reload=http_conf.autoreload,
        log_level="info",
        log_config=None
    )
