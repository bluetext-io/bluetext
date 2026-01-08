"""Couchbase client initialization and deinitialization."""

from fastapi import FastAPI

from couchbase_client import CouchbaseClient
from ..conf.couchbase import get_couchbase_conf
from ..couchbase.models import MODELS
from ..utils.log import get_logger

logger = get_logger(__name__)


async def init_couchbase(app: FastAPI) -> None:
    """Initialize Couchbase client and models."""
    logger.info("Initializing Couchbase client...")
    couchbase_config = get_couchbase_conf()
    app.state.couchbase_client = CouchbaseClient(couchbase_config)
    await app.state.couchbase_client.init_connection()
    logger.info("Couchbase client connected successfully")

    if not MODELS:
        logger.info("No Couchbase models found. You can add models using the add-couchbase-model tool.")
    else:
        logger.info(f"Initializing {len(MODELS)} Couchbase model(s)...")
        for Model in MODELS:
            await Model.initialize(app.state.couchbase_client)
        logger.info(f"All {len(MODELS)} Couchbase model(s) initialized successfully")


async def deinit_couchbase(app: FastAPI) -> None:
    """Close Couchbase client connection."""
    logger.info("Closing Couchbase client connection...")
    await app.state.couchbase_client.close()
    logger.info("Couchbase client connection closed")

