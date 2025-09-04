# FastAPI Application Template
# LLM-optimized template with support for both PostgreSQL and Couchbase
# Uncomment the database configuration you need and set environment variables

import os
import uvicorn
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from config.settings import settings
# Uncomment based on your database choice:
# from clients.postgres_client import postgres_client
# from clients.couchbase_client import couchbase_client

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown tasks including database connections.

    To enable database support:
    1. Uncomment the appropriate client import above
    2. Uncomment the corresponding initialization code below
    3. Set required environment variables
    """
    logger.info("Starting up application...")

    # POSTGRESQL STARTUP - Uncomment to enable PostgreSQL
    # try:
    #     logger.info("Initializing PostgreSQL client...")
    #     await postgres_client.initialize()
    #     logger.info("PostgreSQL client initialized successfully")
    # except Exception as e:
    #     logger.error(f"Failed to initialize PostgreSQL client: {e}")
    #     raise

    # COUCHBASE STARTUP - Uncomment to enable Couchbase
    # try:
    #     logger.info("Initializing Couchbase client...")
    #     await couchbase_client.initialize()
    #     logger.info("Couchbase client initialized successfully")
    # except Exception as e:
    #     logger.error(f"Failed to initialize Couchbase client: {e}")
    #     raise

    logger.info("Application startup complete")

    yield  # Application is running

    logger.info("Shutting down application...")

    # POSTGRESQL SHUTDOWN - Uncomment to enable PostgreSQL
    # try:
    #     logger.info("Closing PostgreSQL client...")
    #     await postgres_client.close()
    #     logger.info("PostgreSQL client closed successfully")
    # except Exception as e:
    #     logger.error(f"Error closing PostgreSQL client: {e}")

    # COUCHBASE SHUTDOWN - Uncomment to enable Couchbase
    # try:
    #     logger.info("Closing Couchbase client...")
    #     await couchbase_client.close()
    #     logger.info("Couchbase client closed successfully")
    # except Exception as e:
    #     logger.error(f"Error closing Couchbase client: {e}")

    logger.info("Application shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="API Template",
    description="LLM-optimized FastAPI template with PostgreSQL and Couchbase support",
    version="1.0.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# CORS Configuration
# Customize these origins based on your frontend applications
origins = [
    "http://localhost:3000",  # React default
    "http://localhost:8080",  # Vue default
    "http://localhost:4200",  # Angular default
    "http://localhost:5173",  # Vite default
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Change to ["*"] for development only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom OpenAPI schema (optional)
def custom_openapi():
    """
    Customize OpenAPI schema.
    Remove this function if you don't need custom OpenAPI behavior.
    """
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    # Add custom OpenAPI modifications here
    # For example, remove security schemes:
    # if "components" in openapi_schema:
    #     openapi_schema["components"].pop("securitySchemes", None)
    # openapi_schema.pop("security", None)

    app.openapi_schema = openapi_schema
    return app.openapi_schema

# Uncomment to use custom OpenAPI
# app.openapi = custom_openapi


# =============================================================================
# ROUTES SETUP
# =============================================================================

# Import and include your route modules here
# Example:
# from routes.users import router as users_router
# from routes.items import router as items_router
# 
# app.include_router(users_router, prefix="/api/users", tags=["users"])
# app.include_router(items_router, prefix="/api/items", tags=["items"])

# Basic health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    Returns application status and database connectivity.
    """
    status = {
        "status": "healthy",
        "databases": {}
    }

    # POSTGRESQL HEALTH CHECK - Uncomment to enable
    # try:
    #     postgres_healthy = await postgres_client.health_check()
    #     status["databases"]["postgres"] = "healthy" if postgres_healthy else "unhealthy"
    # except Exception as e:
    #     status["databases"]["postgres"] = f"error: {str(e)}"

    # COUCHBASE HEALTH CHECK - Uncomment to enable
    # try:
    #     couchbase_healthy = await couchbase_client.health_check()
    #     status["databases"]["couchbase"] = "healthy" if couchbase_healthy else "unhealthy"
    # except Exception as e:
    #     status["databases"]["couchbase"] = f"error: {str(e)}"

    return status


# Example route - remove in production
@app.get("/")
async def root():
    """
    Root endpoint with usage instructions.
    Remove this endpoint when building your actual API.
    """
    return {
        "message": "FastAPI Template",
        "instructions": [
            "1. Choose your database: PostgreSQL or Couchbase",
            "2. Uncomment the corresponding client imports and initialization code",
            "3. Set required environment variables",
            "4. Create your route modules and include them",
            "5. Build your data models using Pydantic",
            "6. Use the database clients for your operations"
        ],
        "docs": "/docs",
        "health": "/health"
    }


# =============================================================================
# APPLICATION STARTUP
# =============================================================================

def main():
    """
    Application entry point.
    Starts the uvicorn server with configuration from settings.
    """
    try:
        # Get HTTP configuration
        http_config = settings.get_http_config()

        logger.info(f"Starting server on {http_config.host}:{http_config.port}")

        # Start the server
        uvicorn.run(
            "main:app",  # Update this path if you move main.py
            host=http_config.host,
            port=http_config.port,
            reload=http_config.reload,
            log_level="info"
        )

    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        raise


if __name__ == "__main__":
    main()


# =============================================================================
# CONFIGURATION REFERENCE
# =============================================================================
"""
ENVIRONMENT VARIABLES:

Required for HTTP server:
- HTTP_HOST (default: 0.0.0.0)
- HTTP_PORT (default: 8000)
- HTTP_RELOAD (default: false)

PostgreSQL (if using PostgreSQL):
- POSTGRES_HOST
- POSTGRES_PORT (default: 5432)
- POSTGRES_DB
- POSTGRES_USER
- POSTGRES_PASSWORD
- POSTGRES_POOL_MIN (default: 1)
- POSTGRES_POOL_MAX (default: 10)

Couchbase (if using Couchbase):
- COUCHBASE_HOST
- COUCHBASE_USERNAME
- COUCHBASE_PASSWORD
- COUCHBASE_BUCKET
- COUCHBASE_PROTOCOL (default: couchbase)

GETTING STARTED:

1. Install dependencies:
   pip install -r requirements.txt
   
2. Choose your database and uncomment dependencies in requirements.txt

3. Uncomment corresponding database client imports and initialization code

4. Set environment variables (create .env file or set in your environment)

5. Create your route modules in src/routes/
   
6. Create your data models in src/models/

7. Import and include your routes in this file

8. Run the application:
   python main.py
   
   Or with uvicorn directly:
   uvicorn main:app --reload

EXAMPLE PROJECT STRUCTURE:
src/
├── main.py                 # This file
├── config/
│   └── settings.py        # Configuration
├── clients/
│   ├── postgres_client.py # PostgreSQL client
│   └── couchbase_client.py# Couchbase client  
├── models/
│   ├── __init__.py
│   └── user.py           # Pydantic models
├── routes/
│   ├── __init__.py
│   ├── users.py          # User routes
│   └── items.py          # Item routes
└── utils/
    ├── __init__.py
    └── helpers.py        # Utility functions
"""
