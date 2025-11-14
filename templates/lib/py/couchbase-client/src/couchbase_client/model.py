"""Base model class for Couchbase models with integrated Pydantic validation."""

from typing import Any, ClassVar, TypeVar
from uuid import UUID

from pydantic import BaseModel


T = TypeVar('T', bound='CouchbaseModel')


class CouchbaseModel(BaseModel):
    """
    Base class for Couchbase models.

    Provides CRUD operations as class methods and auto-derives collection names.

    Example:
        ```python
        class User(CouchbaseModel):
            collection_name = "users"  # Optional, defaults to "users"
            key_type = UUID  # Optional, defaults to UUID

            id: UUID
            name: str
            email: str

        # Usage:
        user = await User.get(client, id=user_id)
        users = await User.list(client, limit=10)
        await User.upsert(client, user)
        ```
    """

    # Class-level configuration - override in subclasses
    collection_name: ClassVar[str] = ""  # Auto-derived from class name if empty
    key_type: ClassVar[type] = UUID  # Default to UUID, can be str, int, etc.

    id: UUID | str | int  # Primary key field - type should match key_type

    @classmethod
    def _get_collection_name(cls) -> str:
        """
        Get the collection name for this model.

        Auto-derives from class name if not explicitly set:
        - UserModel -> "users"
        - ProductModel -> "products"
        - OrderItemModel -> "order_items"
        """
        if cls.collection_name:
            return cls.collection_name

        # Auto-derive: UserModel -> users
        name = cls.__name__
        if name.endswith('Model'):
            name = name[:-5]  # Remove 'Model' suffix

        # Convert PascalCase to snake_case
        import re
        name = re.sub('([a-z0-9])([A-Z])', r'\1_\2', name)
        name = name.lower()

        # Pluralize (simple heuristic)
        if not name.endswith('s'):
            name += 's'

        return name

    @classmethod
    async def initialize(cls, client: 'CouchbaseClient') -> None:
        """
        Initialize the collection for this model.

        Creates the collection if it doesn't exist.
        Called during app startup for all registered models.
        """
        from couchbase_client import CouchbaseClient

        collection_name = cls._get_collection_name()
        scope_name = "_default"
        bucket_name = client._config.bucket

        # Use get_keyspace to create a Keyspace and let auto_create handle the collection
        keyspace = client.get_keyspace(
            collection_name=collection_name,
            scope_name=scope_name,
            bucket_name=bucket_name
        )

        # Ensure the collection exists by attempting to get it (auto_create will handle creation)
        await client.get_collection(keyspace)

    @classmethod
    async def get(cls: type[T], client: 'CouchbaseClient', id: UUID | str | int) -> T | None:
        """
        Get a document by ID.

        Args:
            client: CouchbaseClient instance
            id: Document ID

        Returns:
            Model instance if found, None otherwise
        """
        from couchbase_client import CouchbaseClient

        collection_name = cls._get_collection_name()
        keyspace = client.get_keyspace(collection_name)

        doc_dict = await client.get_document(keyspace, str(id))
        if doc_dict is None:
            return None

        return cls(**doc_dict)

    @classmethod
    async def list(
        cls: type[T],
        client: 'CouchbaseClient',
        limit: int = 100,
        offset: int = 0
    ) -> list[T]:
        """
        List documents with pagination.

        Args:
            client: CouchbaseClient instance
            limit: Maximum number of documents to return
            offset: Number of documents to skip

        Returns:
            List of model instances
        """
        from couchbase_client import CouchbaseClient

        collection_name = cls._get_collection_name()
        keyspace = client.get_keyspace(collection_name)

        query = f"""
            SELECT META().id as id, {collection_name}.*
            FROM `{keyspace.bucket_name}`.`{keyspace.scope_name}`.`{keyspace.collection_name}`
            LIMIT {limit} OFFSET {offset}
        """

        rows = await client.query_documents(query)
        return [cls(**row) for row in rows]

    @classmethod
    async def upsert(cls, client: 'CouchbaseClient', doc: T) -> None:
        """
        Insert or update a document.

        Args:
            client: CouchbaseClient instance
            doc: Model instance to upsert
        """
        from couchbase_client import CouchbaseClient

        collection_name = cls._get_collection_name()
        keyspace = client.get_keyspace(collection_name)

        await client.upsert_document(
            keyspace,
            str(doc.id),
            doc.model_dump(mode='json')
        )

    @classmethod
    async def delete(cls, client: 'CouchbaseClient', id: UUID | str | int) -> None:
        """
        Delete a document by ID.

        Args:
            client: CouchbaseClient instance
            id: Document ID to delete
        """
        from couchbase_client import CouchbaseClient

        collection_name = cls._get_collection_name()
        keyspace = client.get_keyspace(collection_name)

        await client.delete_document(keyspace, str(id))
