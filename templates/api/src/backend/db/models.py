"""
Database models using SQLModel.
"""

from sqlmodel import SQLModel, Field, Session, select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from datetime import datetime


class User(SQLModel, table=True):
    """User model"""
    __table_args__ = {"extend_existing": True}
    
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    name: str
    bio: Optional[str] = None
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None


# Sample CRUD functions

async def create_user(session: AsyncSession, user: User) -> User:
    """Create a new user"""
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def get_user(session: AsyncSession, user_id: int) -> Optional[User]:
    """Get a user by ID"""
    result = await session.exec(select(User).where(User.id == user_id))
    return result.first()


async def get_user_by_email(session: AsyncSession, email: str) -> Optional[User]:
    """Get a user by email"""
    result = await session.exec(select(User).where(User.email == email))
    return result.first()


async def get_users(
    session: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None
) -> List[User]:
    """Get users with pagination and filtering"""
    query = select(User)
    if is_active is not None:
        query = query.where(User.is_active == is_active)
    query = query.offset(skip).limit(limit)
    
    result = await session.exec(query)
    return result.all()


async def update_user(session: AsyncSession, user_id: int, **kwargs) -> Optional[User]:
    """Update a user"""
    result = await session.exec(select(User).where(User.id == user_id))
    user = result.first()
    
    if not user:
        return None
    
    for key, value in kwargs.items():
        if hasattr(user, key):
            setattr(user, key, value)
    
    user.updated_at = datetime.utcnow()
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def delete_user(session: AsyncSession, user_id: int) -> bool:
    """Delete a user"""
    result = await session.exec(select(User).where(User.id == user_id))
    user = result.first()
    
    if not user:
        return False
    
    await session.delete(user)
    await session.commit()
    return True