from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from .utils import log
from . import conf
from .db import create_item, get_item, get_items, update_item, delete_item # noqa: F401

logger = log.get_logger(__name__)
router = APIRouter()

# Contact form model
class ContactForm(BaseModel):
    name: str
    email: str
    message: str

class ContactFormResponse(BaseModel):
    id: str
    message: str

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
    
    # Check Couchbase connectivity if enabled
    if conf.USE_COUCHBASE:
        from .couchbase_client import is_couchbase_connected

        cb_connected = await is_couchbase_connected()
        health_status["couchbase"] = {
            "status": "healthy" if cb_connected else "unhealthy",
            "connected": cb_connected
        }

        if not cb_connected:
            health_status["status"] = "degraded"
    else:
        health_status["couchbase"] = {
            "status": "disabled",
            "message": "Couchbase is disabled (USE_COUCHBASE=False)"
        }

    return health_status

@router.post("/api/contact", response_model=ContactFormResponse)
async def submit_contact_form(contact_form: ContactForm):
    """Submit a contact form."""
    if not conf.USE_COUCHBASE:
        raise HTTPException(status_code=503, detail="Database not configured")

    try:
        from .couchbase_client import create_contact_form
        
        doc_id = await create_contact_form(
            name=contact_form.name,
            email=contact_form.email,
            message=contact_form.message
        )
        
        return ContactFormResponse(
            id=doc_id,
            message="Contact form submitted successfully"
        )
        
    except Exception as e:
        logger.error(f"Failed to submit contact form: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit contact form")

@router.get("/api/contact/{contact_id}")
async def get_contact_form(contact_id: str):
    """Get a contact form by ID."""
    if not conf.USE_COUCHBASE:
        raise HTTPException(status_code=503, detail="Database not configured")

    try:
        from .couchbase_client import get_contact_form
        
        contact = await get_contact_form(contact_id)
        if not contact:
            raise HTTPException(status_code=404, detail="Contact form not found")
        
        return contact
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get contact form: {e}")
        raise HTTPException(status_code=500, detail="Failed to get contact form")

@router.get("/api/contacts")
async def list_contact_forms():
    """Get all contact forms."""
    if not conf.USE_COUCHBASE:
        raise HTTPException(status_code=503, detail="Database not configured")

    try:
        from .couchbase_client import list_all_contact_forms
        
        forms = await list_all_contact_forms()
        return {"forms": forms, "count": len(forms)}
        
    except Exception as e:
        logger.error(f"Failed to list contact forms: {e}")
        raise HTTPException(status_code=500, detail="Failed to list contact forms")

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
