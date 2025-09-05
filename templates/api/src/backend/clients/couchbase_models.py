"""
Couchbase document models and operations.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
import uuid


class CouchbaseUser(BaseModel):
    """User document model for Couchbase"""
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    name: str
    bio: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Sample CRUD operations for Couchbase

async def create_user(client, user: CouchbaseUser) -> str:
    """Create a new user in Couchbase"""
    keyspace = client.get_keyspace("users")
    user_dict = user.dict()
    user_id = user_dict.pop('id')  # Use id as document key
    return await client.insert_document(keyspace, user_dict, key=user_id)


async def get_user(client, user_id: str) -> Optional[CouchbaseUser]:
    """Get a user by ID from Couchbase"""
    keyspace = client.get_keyspace("users")
    doc = await client.get_document(keyspace, user_id)
    if doc:
        doc['id'] = user_id  # Add the key back as id
        return CouchbaseUser(**doc)
    return None


async def get_user_by_email(client, email: str) -> Optional[CouchbaseUser]:
    """Get a user by email using N1QL query"""
    query = """
        SELECT META().id as id, *
        FROM `main`.`_default`.`users` u
        WHERE u.email = $email
        LIMIT 1
    """
    results = await client.query_documents(query, {"email": email})
    if results:
        user_data = results[0]
        return CouchbaseUser(**user_data)
    return None


async def list_users(client, limit: int = 100, offset: int = 0) -> List[CouchbaseUser]:
    """List users with pagination"""
    query = f"""
        SELECT META().id as id, *
        FROM `main`.`_default`.`users`
        ORDER BY created_at DESC
        LIMIT {limit} OFFSET {offset}
    """
    results = await client.query_documents(query)
    return [CouchbaseUser(**doc) for doc in results]


async def update_user(client, user_id: str, updates: Dict[str, Any]) -> Optional[CouchbaseUser]:
    """Update a user document"""
    keyspace = client.get_keyspace("users")
    
    # Get existing document
    existing = await client.get_document(keyspace, user_id)
    if not existing:
        return None
    
    # Apply updates
    existing.update(updates)
    existing['updated_at'] = datetime.utcnow().isoformat()
    
    # Update document
    success = await client.update_document(keyspace, user_id, existing)
    if success:
        existing['id'] = user_id
        return CouchbaseUser(**existing)
    return None


async def delete_user(client, user_id: str) -> bool:
    """Delete a user document"""
    keyspace = client.get_keyspace("users")
    return await client.delete_document(keyspace, user_id)


async def search_users(client, search_term: str, limit: int = 10) -> List[CouchbaseUser]:
    """Search users by name or email"""
    query = """
        SELECT META().id as id, *
        FROM `main`.`_default`.`users` u
        WHERE LOWER(u.name) LIKE LOWER($search)
           OR LOWER(u.email) LIKE LOWER($search)
        LIMIT $limit
    """
    search_pattern = f"%{search_term}%"
    results = await client.query_documents(
        query, 
        {"search": search_pattern, "limit": limit}
    )
    return [CouchbaseUser(**doc) for doc in results]


async def count_active_users(client) -> int:
    """Count active users"""
    query = """
        SELECT COUNT(*) as count
        FROM `main`.`_default`.`users` u
        WHERE u.is_active = true
    """
    results = await client.query_documents(query)
    return results[0]['count'] if results else 0