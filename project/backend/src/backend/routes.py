from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from .utils import log
from . import conf
from .db import create_item, get_item, get_items, update_item, delete_item # noqa: F401
from .db.models import Contact

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

# Contact form endpoints
class ContactRequest(BaseModel):
    name: str
    email: str
    subject: str
    message: str

@router.post("/contact", response_model=Contact)
async def submit_contact_form(contact_data: ContactRequest):
    """Submit a contact form."""
    logger.info(f"Received contact form submission: {contact_data}")
    
    if not conf.USE_POSTGRES:
        raise HTTPException(status_code=503, detail="Database not configured")

    try:
        # Create a Contact instance from the request data
        contact = Contact(
            name=contact_data.name,
            email=contact_data.email,
            subject=contact_data.subject,
            message=contact_data.message,
            created_at=datetime.utcnow()
        )
        
        logger.info(f"Created Contact instance: {contact}")
        
        # Save to database
        saved_contact = await create_item(contact)
        logger.info(f"Contact form submitted by {contact_data.name} ({contact_data.email})")
        return saved_contact
    except Exception as e:
        logger.error(f"Failed to save contact form: {e}")
        logger.error(f"Exception type: {type(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to save contact form: {str(e)}")

@router.get("/contacts", response_model=List[Contact])
async def list_contacts(limit: int = 100, offset: int = 0):
    """List all contact form submissions with pagination."""
    if not conf.USE_POSTGRES:
        raise HTTPException(status_code=503, detail="Database not configured")

    try:
        return await get_items(Contact, limit=limit, offset=offset)
    except Exception as e:
        logger.error(f"Failed to retrieve contacts: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve contacts")

@router.get("/contacts/{contact_id}", response_model=Contact)
async def get_contact(contact_id: int):
    """Get a specific contact form submission by ID."""
    if not conf.USE_POSTGRES:
        raise HTTPException(status_code=503, detail="Database not configured")

    try:
        contact = await get_item(Contact, contact_id)
        if not contact:
            raise HTTPException(status_code=404, detail="Contact not found")
        return contact
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve contact {contact_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve contact")

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
