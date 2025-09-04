# Base Pydantic Models
# Common models and base classes for your application data structures

from datetime import datetime
from typing import Optional, Any, Dict
from pydantic import BaseModel, Field
from uuid import uuid4

# Uncomment for PostgreSQL SQLModel support
# from sqlmodel import SQLModel


class TimestampMixin(BaseModel):
    """Mixin for models that need timestamp fields"""
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")


class ResponseModel(BaseModel):
    """Base response model with success status"""
    success: bool = True
    message: str = "Operation completed successfully"
    data: Optional[Any] = None


class ErrorResponse(BaseModel):
    """Standard error response model"""
    success: bool = False
    message: str
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class PaginationParams(BaseModel):
    """Standard pagination parameters"""
    page: int = Field(default=1, ge=1, description="Page number (1-based)")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")
    
    @property
    def offset(self) -> int:
        """Calculate offset for database queries"""
        return (self.page - 1) * self.page_size


class PaginatedResponse(BaseModel):
    """Paginated response wrapper"""
    items: list
    total: int
    page: int
    page_size: int
    has_next: bool
    has_prev: bool
    
    @classmethod
    def create(cls, items: list, total: int, params: PaginationParams):
        """Create paginated response from items and pagination params"""
        return cls(
            items=items,
            total=total,
            page=params.page,
            page_size=params.page_size,
            has_next=(params.page * params.page_size) < total,
            has_prev=params.page > 1
        )


# =============================================================================
# EXAMPLE MODELS - Remove or modify for your use case
# =============================================================================

class UserBase(BaseModel):
    """Base user model with common fields"""
    name: str = Field(..., description="User's full name", max_length=100)
    email: str = Field(..., description="User's email address", max_length=255)


class UserCreate(UserBase):
    """Model for creating a new user"""
    password: str = Field(..., description="User's password", min_length=8)


class UserUpdate(BaseModel):
    """Model for updating user data"""
    name: Optional[str] = Field(None, max_length=100)
    email: Optional[str] = Field(None, max_length=255)


class UserResponse(UserBase, TimestampMixin):
    """User response model (excludes sensitive data like password)"""
    id: str = Field(description="Unique user identifier")
    
    class Config:
        from_attributes = True  # For SQLModel compatibility


# POSTGRESQL SQLMODEL VERSION - Uncomment to use with PostgreSQL
# class UserTable(SQLModel, table=True):
#     """SQLModel for PostgreSQL user table"""
#     __tablename__ = "users"
#     __table_args__ = {"extend_existing": True}
#     
#     id: Optional[int] = Field(default=None, primary_key=True)
#     name: str = Field(max_length=100, index=True)
#     email: str = Field(max_length=255, unique=True, index=True)
#     password_hash: str = Field(max_length=255)  # Store hashed passwords only
#     created_at: datetime = Field(default_factory=datetime.utcnow)
#     updated_at: Optional[datetime] = None


class ItemBase(BaseModel):
    """Base item model"""
    name: str = Field(..., description="Item name", max_length=100)
    description: Optional[str] = Field(None, description="Item description", max_length=500)
    price: Optional[float] = Field(None, description="Item price", ge=0)
    is_active: bool = Field(default=True, description="Whether item is active")


class ItemCreate(ItemBase):
    """Model for creating a new item"""
    pass


class ItemUpdate(BaseModel):
    """Model for updating item data"""
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    price: Optional[float] = Field(None, ge=0)
    is_active: Optional[bool] = None


class ItemResponse(ItemBase, TimestampMixin):
    """Item response model"""
    id: str = Field(description="Unique item identifier")
    
    class Config:
        from_attributes = True


# COUCHBASE DOCUMENT VERSION
class CouchbaseDocument(BaseModel):
    """Base model for Couchbase documents"""
    document_type: str = Field(description="Document type identifier")
    
    @classmethod
    def from_couchbase_result(cls, key: str, content: dict):
        """Create model instance from Couchbase query result"""
        return cls(id=key, **content)
    
    def to_couchbase_document(self) -> dict:
        """Convert to dictionary for Couchbase storage"""
        data = self.model_dump()
        data.pop('id', None)  # Remove ID as it's stored as document key
        return data


# =============================================================================
# USAGE EXAMPLES AND TEMPLATES
# =============================================================================
"""
CREATING YOUR OWN MODELS:

1. For general API data models, inherit from BaseModel:
   
   class MyModel(BaseModel):
       field1: str
       field2: int = Field(default=0, description="My field")

2. For timestamped models, use TimestampMixin:
   
   class MyTimestampedModel(BaseModel, TimestampMixin):
       data: str

3. For PostgreSQL with SQLModel, create both Pydantic and table models:
   
   class MyModelBase(BaseModel):
       name: str
   
   class MyModelCreate(MyModelBase):
       pass
   
   class MyModelResponse(MyModelBase, TimestampMixin):
       id: int
   
   class MyModelTable(SQLModel, table=True):
       __tablename__ = "my_models"
       id: Optional[int] = Field(default=None, primary_key=True)
       name: str

4. For Couchbase, inherit from CouchbaseDocument:
   
   class MyDocument(CouchbaseDocument):
       document_type: str = Field(default="my_document")
       name: str
       data: dict

5. Always use Field() for documentation and validation:
   
   field: str = Field(..., description="Required field", max_length=50)
   optional_field: Optional[int] = Field(None, description="Optional field", ge=0)
"""