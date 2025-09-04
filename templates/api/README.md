# FastAPI Template - LLM Optimized

A comprehensive FastAPI template optimized for Large Language Models (LLMs) to easily extend and build upon. This template supports both PostgreSQL and Couchbase databases with generic helper functions for rapid development.

## 🚀 Features

- **Database Agnostic**: Support for both PostgreSQL and Couchbase
- **LLM Optimized**: Extensive comments and documentation for easy AI comprehension
- **Generic Clients**: Ready-to-use database clients with common operations
- **Pydantic Models**: Full Pydantic integration for data validation
- **Commented Configuration**: All database configs are commented - just uncomment what you need
- **Helper Functions**: Generic utilities for common operations
- **Production Ready**: Proper error handling, logging, and connection pooling

## 📁 Project Structure

```
api-template/
├── src/
│   ├── main.py                 # FastAPI application with commented database configs
│   ├── config/
│   │   └── settings.py         # Configuration management
│   ├── clients/
│   │   ├── postgres_client.py  # PostgreSQL client with helper functions
│   │   └── couchbase_client.py # Couchbase client with caching
│   ├── models/
│   │   ├── __init__.py
│   │   └── base.py            # Base Pydantic models and examples
│   └── utils/
│       └── helpers.py         # Common utility functions
├── requirements.txt           # Dependencies (commented by database type)
└── README.md                 # This file
```

## 🛠️ Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Choose Your Database

**For PostgreSQL:**
1. Uncomment PostgreSQL dependencies in `requirements.txt`
2. Install: `pip install sqlmodel psycopg[binary,pool]`
3. Uncomment PostgreSQL imports and configs in `src/main.py`
4. Uncomment `get_postgres_config` in `src/config/settings.py`

**For Couchbase:**
1. Uncomment Couchbase dependencies in `requirements.txt`
2. Install: `pip install couchbase`
3. Uncomment Couchbase imports and configs in `src/main.py`
4. Uncomment `get_couchbase_config` in `src/config/settings.py`

### 3. Set Environment Variables

**PostgreSQL:**
```bash
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_DB=mydb
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=password
```

**Couchbase:**
```bash
export COUCHBASE_HOST=localhost
export COUCHBASE_USERNAME=admin
export COUCHBASE_PASSWORD=password
export COUCHBASE_BUCKET=mybucket
export COUCHBASE_PROTOCOL=couchbase
```

### 4. Run the Application

```bash
python src/main.py
```

Or with uvicorn:
```bash
uvicorn src.main:app --reload
```

Visit `http://localhost:8000/docs` for the API documentation.

## 💾 Database Usage

### PostgreSQL Example

```python
from clients.postgres_client import postgres_client

# Insert a record
user_id = await postgres_client.insert_one('users', {
    'name': 'John Doe',
    'email': 'john@example.com'
})

# Find by ID
user = await postgres_client.find_by_id('users', user_id)

# Update record
await postgres_client.update_one('users', user_id, {'name': 'John Smith'})

# Custom query
results = await postgres_client.execute_query(
    "SELECT * FROM users WHERE email = %(email)s",
    {'email': 'john@example.com'}
)
```

### Couchbase Example

```python
from clients.couchbase_client import couchbase_client

# Create keyspace
users_keyspace = couchbase_client.get_keyspace("users")

# Insert document
user_id = await couchbase_client.insert_document(users_keyspace, {
    'name': 'John Doe',
    'email': 'john@example.com'
})

# Get document
user = await couchbase_client.get_document(users_keyspace, user_id)

# N1QL Query
results = await couchbase_client.query_documents(
    f"SELECT * FROM `{users_keyspace}` WHERE email = $email",
    {"email": "john@example.com"}
)
```

## 📝 Creating Your Models

The template uses Pydantic throughout. Example models are in `src/models/base.py`:

```python
from pydantic import BaseModel, Field
from models.base import TimestampMixin

class UserCreate(BaseModel):
    name: str = Field(..., max_length=100)
    email: str = Field(..., max_length=255)

class UserResponse(UserCreate, TimestampMixin):
    id: str
    
    class Config:
        from_attributes = True
```

## 🔧 Configuration

All configuration is in `src/config/settings.py`. The template uses environment variables with sensible defaults:

- `HTTP_HOST` (default: 0.0.0.0)
- `HTTP_PORT` (default: 8000)
- `HTTP_RELOAD` (default: false)

Database-specific variables are documented in the settings file.

## 🧰 Utility Functions

Common utilities are in `src/utils/helpers.py`:

- Password hashing and verification
- UUID generation
- Pagination helpers
- SQL query builders
- Datetime utilities
- Data cleaning functions

## 🏗️ Building Your API

### 1. Create Route Modules

```python
# src/routes/users.py
from fastapi import APIRouter, Depends
from models.base import UserCreate, UserResponse

router = APIRouter()

@router.post("/", response_model=UserResponse)
async def create_user(user: UserCreate):
    # Use database client to create user
    pass
```

### 2. Include Routes in Main App

```python
# In src/main.py
from routes.users import router as users_router

app.include_router(users_router, prefix="/api/users", tags=["users"])
```

### 3. Add Your Models

Create your Pydantic models in `src/models/` following the examples in `base.py`.

## 🔍 Health Checks

The template includes health check endpoints that verify database connectivity:

```bash
curl http://localhost:8000/health
```

## 📚 LLM Usage Instructions

This template is optimized for LLM understanding and extension:

1. **All configurations are commented** - uncomment only what you need
2. **Extensive inline documentation** - every function and class is documented
3. **Generic helper functions** - common operations are pre-built
4. **Example models** - templates for your own data structures
5. **Clear separation of concerns** - database, models, routes, and config are separate

### For LLMs extending this template:

1. Read the configuration in `src/config/settings.py`
2. Choose database by uncommenting appropriate sections
3. Use the generic client methods for database operations
4. Follow the Pydantic model patterns in `src/models/base.py`
5. Create routes following FastAPI patterns
6. Utilize helper functions in `src/utils/helpers.py`

## 🚀 Production Deployment

1. Set `HTTP_RELOAD=false` in production
2. Use environment variables for all sensitive configuration
3. Consider using a process manager like gunicorn:

```bash
pip install gunicorn
gunicorn src.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

## 📄 License

This template is provided as-is for educational and development purposes.

## 🤝 Contributing

This template is designed to be extended by LLMs and developers. Feel free to modify and adapt it for your specific use cases.