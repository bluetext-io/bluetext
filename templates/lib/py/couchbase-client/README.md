# Couchbase Client Library

A Python library for working with Couchbase databases, featuring async support and integrated Pydantic validation.

## Features

- **Async/await support** - Built on top of the Couchbase Python SDK with full async capabilities
- **Pydantic integration** - Automatic validation and serialization of documents
- **Base model class** - `CouchbaseModel` provides CRUD operations and collection management
- **Type-safe** - Full type hints for better IDE support and type checking

## Overview

This library provides async Couchbase database integration for Python applications. If you're reading this, the library has already been integrated into your API project.

## Components

### CouchbaseClient

Low-level client for Couchbase operations:

```python
from couchbase_client import CouchbaseClient, CouchbaseConf

config = CouchbaseConf(
    host="couchbase",
    username="user",
    password="password",
    bucket="main",
    protocol="couchbase"
)

client = CouchbaseClient(config)
await client.init_connection()

# Low-level operations
doc = await client.get_document(keyspace, doc_id)
await client.upsert_document(keyspace, doc_id, data)
await client.delete_document(keyspace, doc_id)
```

### CouchbaseModel

Base class for defining Couchbase models with Pydantic validation and CRUD operations:

## Defining Models

**Important: Always use the MCP tool for proper model setup:**

```mcp
__polytope__{{ api-name }}-add-couchbase-model(name: "user")
```

Replace `{{ api-name }}` with your actual API subproject name.

The tool will:
- Generate a properly structured model file
- Add the model import to `src/backend/couchbase/models/__init__.py`
- Register the model in the `MODELS` list for automatic initialization

Example generated model:

```python
from typing import ClassVar
from uuid import UUID
from couchbase_client import CouchbaseModel

class UserModel(CouchbaseModel):
    """Model for user documents."""

    # Optional: Override defaults
    # collection_name: ClassVar[str] = "users"  # Auto-derived from class name
    # key_type: ClassVar[type] = UUID  # Defaults to UUID

    # Document fields
    id: UUID
    name: str
    email: str
    created_at: datetime
```

### Usage in Your API

Once integrated, models provide class methods for all CRUD operations:

```python
# Example usage in routes
user = await UserModel.get(client, id=user_id)
users = await UserModel.list(client, limit=50, offset=0)
await UserModel.upsert(client, user)
await UserModel.delete(client, id=user_id)
```

The API setup handles:
- Model registration and discovery
- Collection initialization during startup
- Hot reload support for automatic schema updates

## Migration from Old Pattern

If you have existing manually-created models using the old two-class pattern (`{Model}Doc` + `{Model}Model`):

1. **Use the MCP tool** - Always use the tool to create new models for proper setup:
   ```mcp
   __polytope__{{ api-name }}-add-couchbase-model(name: "model-name")
   ```

2. **Clean up old models** - Remove manually created model files that don't follow the new single-class pattern

3. **Update code references** - Change your code to use the new class method API:
   ```python
   # Old pattern (deprecated)
   model = UserModel(client)
   await model.initialize()
   user = await model.get(user_id)

   # New pattern (recommended)
   user = await UserModel.get(client, id=user_id)
   ```

## API Reference

### CouchbaseModel Base Class

All models inherit from `CouchbaseModel` which provides:

#### Class Methods

- `initialize(client: CouchbaseClient) -> None` - Create collection if it doesn't exist
- `get(client: CouchbaseClient, id: UUID | str | int) -> T | None` - Get document by ID
- `list(client: CouchbaseClient, limit: int = 100, offset: int = 0) -> list[T]` - List documents with pagination
- `upsert(client: CouchbaseClient, doc: T) -> None` - Insert or update document
- `delete(client: CouchbaseClient, id: UUID | str | int) -> None` - Delete document by ID

#### Class Attributes (Override in Subclasses)

- `collection_name: ClassVar[str]` - Override to set custom collection name (auto-derived if not set)
- `key_type: ClassVar[type]` - Override to set key type (defaults to `UUID`)

## Configuration

The `CouchbaseConf` class requires the following connection parameters:

- `host` - Couchbase server host
- `username` - Username for authentication
- `password` - Password for authentication
- `bucket` - Bucket name
- `protocol` - Protocol to use (typically `couchbase` or `couchbases`)

When integrated with the API, these are automatically configured via environment variables.
