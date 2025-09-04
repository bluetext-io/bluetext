from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from .utils import log
from . import conf
from .db import create_item, get_item, get_items, update_item, delete_item # noqa: F401

logger = log.get_logger(__name__)
router = APIRouter()

@router.get("/")
async def root():
    return {"message": "Hello World"}

@router.get("/health")
async def health_check():
    """Health check endpoint."""
    health_status = {
        "status": "healthy",
        "service": "backend",
    }

    # Check database connectivity if enabled
    if conf.USE_POSTGRES:
        from .db import is_connected

        db_connected = await is_connected()
        health_status["database"] = {
            "status": "healthy" if db_connected else "unhealthy",
            "connected": db_connected
        }

        if not db_connected:
            health_status["status"] = "degraded"
    else:
        health_status["database"] = {
            "status": "disabled",
            "message": "PostgreSQL is disabled (USE_POSTGRES=False)"
        }

    return health_status

# Database route examples (uncomment and modify when you have models)
#
# from .db import get_connection, create_item, get_item, get_items
# from .db.models import User  # Import your models
#
# @router.post("/users", response_model=User)
# async def create_user(user: User):
#     """Create a new user."""
#     if not conf.USE_POSTGRES:
#         raise HTTPException(status_code=503, detail="Database not configured")
#
#     try:
#         return await create_item(user)
#     except Exception as e:
#         logger.error(f"Failed to create user: {e}")
#         raise HTTPException(status_code=500, detail="Failed to create user")
#
# @router.get("/users/{user_id}", response_model=User)
# async def read_user(user_id: int):
#     """Get a user by ID."""
#     if not conf.USE_POSTGRES:
#         raise HTTPException(status_code=503, detail="Database not configured")
#
#     user = await get_item(User, user_id)
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")
#     return user
#
# @router.get("/users", response_model=List[User])
# async def list_users(limit: int = 100, offset: int = 0):
#     \"\"\"List all users with pagination.\"\"\"
#     if not conf.USE_POSTGRES:
#         raise HTTPException(status_code=503, detail="Database not configured")
#
#     return await get_items(User, limit=limit, offset=offset)
#
