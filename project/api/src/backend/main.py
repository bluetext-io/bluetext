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
        from .db import init_db, close_db
        await init_db()
    
    # Initialize Couchbase connection if enabled
    if conf.USE_COUCHBASE:
        from .couchbase_client import init_couchbase, close_couchbase
        await init_couchbase()

    yield

    # Clean up database connection if enabled
    if conf.USE_POSTGRES:
        await close_db()
    
    # Clean up Couchbase connection if enabled
    if conf.USE_COUCHBASE:
        from .couchbase_client import close_couchbase
        await close_couchbase()

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
