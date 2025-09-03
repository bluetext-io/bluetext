from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

# Add your SQLModel models here
# Example:
#
# class User(SQLModel, table=True):
#     __table_args__ = {"extend_existing": True}  # Prevents duplicate registration errors
#
#     id: Optional[int] = Field(default=None, primary_key=True)
#     email: str = Field(unique=True, index=True)
#     name: str
#     created_at: datetime = Field(default_factory=datetime.utcnow)
#     updated_at: Optional[datetime] = None
#
# class Post(SQLModel, table=True):
#     __table_args__ = {"extend_existing": True}  # Prevents duplicate registration errors
#
#     id: Optional[int] = Field(default=None, primary_key=True)
#     title: str
#     content: str
#     user_id: int = Field(foreign_key="user.id")
#     created_at: datetime = Field(default_factory=datetime.utcnow)
