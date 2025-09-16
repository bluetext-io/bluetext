"""
Database models using SQLModel.

IMPORTANT: All SQLModel table classes defined in this file are automatically
registered when this module is imported. The app's lifespan function in main.py
imports this module and creates the tables during startup.

To add a new model:
1. Define your class with SQLModel and table=True
2. The table will be automatically created on next startup
3. Add any necessary database functions below the model definitions
"""

from sqlmodel import SQLModel, Field, select # noqa
from sqlalchemy.ext.asyncio import AsyncSession # noqa
from typing import Optional # noqa
from datetime import datetime # noqa


# Define your models here. Example:
#
# class User(SQLModel, table=True):
#     id: Optional[int] = Field(default=None, primary_key=True)
#     email: str = Field(unique=True, index=True)
#     name: str
#     created_at: datetime = Field(default_factory=datetime.utcnow)
#
#
# # Define your database functions here. Example:
#
# async def create_user(session: AsyncSession, user: User) -> User:
#     """Create a new user - DO NOT call session.commit() here!
#     
#     The DBSession dependency in routes/utils.py handles all commits automatically.
#     Only use session.add(), session.execute(), etc. Never commit or rollback.
#     """
#     session.add(user)
#     await session.flush()  # Get the ID without committing
#     return user
