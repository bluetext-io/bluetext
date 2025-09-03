# Backend API

A FastAPI application with SQLModel and PostgreSQL support.

## Features

- **FastAPI** web framework with async support
- **SQLModel** for type-safe database models (Pydantic + SQLAlchemy)
- **PostgreSQL** with psycopg3 async driver and connection pooling
- Automatic table creation on startup
- Auto-reconnection on database connection loss
- Health check endpoint with database status

## Database Setup

### Automatic Table Creation

When you:

1. **Add new SQLModel models** to `src/backend/db/models.py`
2. **Start the application**

The system will:
- ✅ Automatically create all tables and indexes
- ✅ Handle schema mismatches by dropping and recreating tables (in development)

**No manual commands needed!** Just define your models and run the app.

⚠️ **Note**: Schema changes to existing tables will trigger a drop and recreate. In production, you should manage schema migrations manually.

### Enabling/Disabling PostgreSQL

PostgreSQL is controlled by the `USE_POSTGRES` flag in `src/backend/conf.py`:

```python
# Set to False if you don't want to use PostgreSQL
USE_POSTGRES = True  # Change to False to disable database
```

When `USE_POSTGRES = False`:
- The app runs without any database
- All database endpoints return 503
- Health check shows database as "disabled"

## Adding Models

Add your SQLModel models to `src/backend/db/models.py`:

```python
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Post(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    content: str
    user_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

**Tables are created automatically** when you start the app!

## Creating API Endpoints

Example endpoints are provided in `src/backend/routes.py`. Uncomment and modify as needed:

```python
from .db import create_item, get_item, get_items
from .db.models import User

@router.post("/users")
async def create_user(user: User):
    return await create_item(user)

@router.get("/users/{user_id}")
async def get_user(user_id: int):
    return await get_item(User, user_id)

@router.get("/users")
async def list_users(limit: int = 100):
    return await get_items(User, limit=limit)
```

## Database Utilities

The template includes helper functions in `db/utils.py`:

- `create_item(model)` - Create a new record
- `get_item(Model, id)` - Get by ID
- `get_items(Model, limit, offset, where)` - List with filtering
- `update_item(Model, id, updates)` - Update by ID
- `delete_item(Model, id)` - Delete by ID
- `bulk_create(Model, items)` - Bulk insert
- `execute_query(sql, params)` - Raw SQL queries
- `execute_transaction(operations)` - Transaction support

## Notes for AI Coding Assistants

- **Database tables are created automatically** - just add models to `models.py`
- **Tables are recreated on schema changes** - be careful in production
- **Connection retry** is built-in - the app will reconnect if database goes down
- **Use the provided utilities** in `db/utils.py` for database operations
- **Check `USE_POSTGRES`** flag before using database features
- **SQL injection protection** is built into all utility functions
