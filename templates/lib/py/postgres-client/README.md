# PostgreSQL Client Library

A lightweight async PostgreSQL client library for FastAPI applications with SQLModel support.

## Features

- Async connection pooling with automatic reconnection
- SQLModel integration for ORM operations
- Automatic table creation and migration
- Health check endpoint support
- Transaction management with automatic commit/rollback

## Installation

This library is installed automatically when you run the `api-add-postgres-client` tool in your API service.

## Usage

### Basic Setup

The library is automatically initialized when added to your API service. Configuration is handled via environment variables:

- `POSTGRES_HOST`: Database host (default: "postgres")
- `POSTGRES_PORT`: Database port (default: 5432)
- `POSTGRES_DB`: Database name (default: "postgres")
- `POSTGRES_USER`: Database user (default: "postgres")
- `POSTGRES_PASSWORD`: Database password (default: "postgres")
- `POSTGRES_POOL_MIN`: Minimum pool size (default: 1)
- `POSTGRES_POOL_MAX`: Maximum pool size (default: 10)

### Using in Routes

```python
from ..routes.utils import DBSession
from sqlmodel import select
from ..db.models import User

@router.get('/users')
async def get_users(session=Depends(DBSession)):
    result = await session.execute(select(User))
    return result.scalars().all()

@router.post('/users')
async def create_user(user: UserCreate, session=Depends(DBSession)):
    db_user = User.model_validate(user)
    session.add(db_user)
    await session.flush()  # Get the ID without committing
    return db_user
```

### Direct Client Access

```python
from postgres_client import PostgresClient, PostgresConf

# Get the client from FastAPI app state
client = request.app.state.postgres_client

# Use the session context manager
async with client.get_session() as session:
    # Your database operations here
    pass

# Raw SQL access
async with client.get_connection() as conn:
    async with conn.cursor() as cur:
        await cur.execute("SELECT * FROM users")
        results = await cur.fetchall()
```

## Adding Models

Use the polytope tool to scaffold new models:

```
__polytope__run(tool: api-add-postgres-model, name: <model-name>)
```

This will create a new model file with CRUD operations and automatic migration support.