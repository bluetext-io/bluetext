# Couchbase Database Client
# Generic client for Couchbase operations with connection caching and helper functions
# To use: uncomment the Couchbase dependencies in requirements.txt and uncomment
# the couchbase_config in config/settings.py

import uuid
import logging
from datetime import timedelta
from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass

# Uncomment these imports when using Couchbase
# from couchbase.auth import PasswordAuthenticator
# from couchbase.cluster import Cluster
# from couchbase.options import ClusterOptions, QueryOptions
# from couchbase.exceptions import DocumentNotFoundException, BucketNotFoundException
# from couchbase.result import MutationResult

from config.settings import settings

logger = logging.getLogger(__name__)


@dataclass
class Keyspace:
    """
    Represents a Couchbase keyspace (bucket.scope.collection).
    Provides convenient methods for common operations.
    """
    bucket_name: str
    scope_name: str
    collection_name: str

    @classmethod
    def from_string(cls, keyspace: str) -> 'Keyspace':
        """
        Create Keyspace from string format 'bucket.scope.collection'.

        Args:
            keyspace: String in format 'bucket.scope.collection'

        Returns:
            Keyspace instance

        Raises:
            ValueError: If keyspace format is invalid
        """
        parts = keyspace.split('.')
        if len(parts) != 3:
            raise ValueError(
                "Invalid keyspace format. Expected 'bucket_name.scope_name.collection_name', "
                f"got '{keyspace}'"
            )
        return cls(*parts)

    def __str__(self) -> str:
        """String representation of keyspace"""
        return f"{self.bucket_name}.{self.scope_name}.{self.collection_name}"


class CouchbaseClient:
    """
    Generic Couchbase client with connection caching and helper functions.

    This client provides:
    - Cached cluster connection
    - Generic CRUD operations for documents
    - N1QL query execution
    - Keyspace management
    - Bulk operations

    USAGE:
    1. Uncomment Couchbase dependencies in requirements.txt
    2. Uncomment get_couchbase_config in config/settings.py
    3. Set required environment variables
    4. Initialize client: couchbase_client = CouchbaseClient()
    5. Call await couchbase_client.initialize() during app startup
    6. Use helper methods for database operations
    """

    def __init__(self):
        self._cluster = None
        self._config = None

    async def initialize(self):
        """
        Initialize the Couchbase client with cluster connection.
        Call this during application startup.
        """
        # Uncomment to enable Couchbase
        # self._config = settings.get_couchbase_config()
        # self._cluster = await self._create_cluster()
        # logger.info("Couchbase client initialized")
        pass

    async def close(self):
        """
        Close the Couchbase client and cleanup connections.
        Call this during application shutdown.
        """
        # Uncomment to enable Couchbase
        # if self._cluster:
        #     self._cluster = None
        #     logger.info("Couchbase client closed")
        pass

    # def _create_cluster(self):
    #     """Create and cache cluster connection"""
    #     auth = PasswordAuthenticator(self._config.username, self._config.password)
    #
    #     cluster_options = ClusterOptions(auth)
    #     if self._config.protocol == "couchbases":
    #         cluster_options.verify_credentials = True
    #
    #     cluster = Cluster(self._config.get_connection_url(), cluster_options)
    #     cluster.wait_until_ready(timedelta(seconds=30))
    #
    #     return cluster

    def get_cluster(self):
        """
        Get the cached cluster connection.

        Returns:
            Couchbase Cluster instance

        Raises:
            RuntimeError: If client not initialized
        """
        # Uncomment to enable Couchbase
        # if not self._cluster:
        #     raise RuntimeError("Couchbase client not initialized")
        # return self._cluster
        raise NotImplementedError("Couchbase client not enabled. Uncomment code to use.")

    def get_keyspace(self, collection_name: str, scope_name: str = "_default", bucket_name: Optional[str] = None) -> Keyspace:
        """
        Create a Keyspace instance for database operations.

        Args:
            collection_name: Name of the collection
            scope_name: Name of the scope (defaults to "_default")
            bucket_name: Name of the bucket (defaults to configured bucket)

        Returns:
            Keyspace instance for performing operations
        """
        # Uncomment to enable Couchbase
        # if bucket_name is None:
        #     bucket_name = self._config.bucket
        # return Keyspace(bucket_name, scope_name, collection_name)
        raise NotImplementedError("Couchbase client not enabled. Uncomment code to use.")

    def get_collection(self, keyspace: Keyspace):
        """
        Get a Couchbase Collection object from keyspace.

        Args:
            keyspace: Keyspace instance

        Returns:
            Couchbase Collection object
        """
        # Uncomment to enable Couchbase
        # cluster = self.get_cluster()
        # bucket = cluster.bucket(keyspace.bucket_name)
        # scope = bucket.scope(keyspace.scope_name)
        # return scope.collection(keyspace.collection_name)
        raise NotImplementedError("Couchbase client not enabled. Uncomment code to use.")

    async def insert_document(self, keyspace: Keyspace, document: Dict[str, Any], key: Optional[str] = None) -> str:
        """
        Insert a document into a collection.

        Args:
            keyspace: Keyspace where to insert document
            document: Document data as dictionary
            key: Document key (generates UUID if not provided)

        Returns:
            Document key of inserted document
        """
        # Uncomment to enable Couchbase
        # if key is None:
        #     key = str(uuid.uuid4())
        #
        # collection = self.get_collection(keyspace)
        # collection.insert(key, document)
        # return key
        raise NotImplementedError("Couchbase client not enabled. Uncomment code to use.")

    async def get_document(self, keyspace: Keyspace, key: str) -> Optional[Dict[str, Any]]:
        """
        Get a document by key.

        Args:
            keyspace: Keyspace where document is stored
            key: Document key

        Returns:
            Document data as dictionary, or None if not found
        """
        # Uncomment to enable Couchbase
        # try:
        #     collection = self.get_collection(keyspace)
        #     result = collection.get(key)
        #     return result.content_as[dict]
        # except DocumentNotFoundException:
        #     return None
        raise NotImplementedError("Couchbase client not enabled. Uncomment code to use.")

    async def update_document(self, keyspace: Keyspace, key: str, document: Dict[str, Any]) -> bool:
        """
        Update a document by key.

        Args:
            keyspace: Keyspace where document is stored
            key: Document key
            document: New document data

        Returns:
            True if document was updated, False if not found
        """
        # Uncomment to enable Couchbase
        # try:
        #     collection = self.get_collection(keyspace)
        #     collection.replace(key, document)
        #     return True
        # except DocumentNotFoundException:
        #     return False
        raise NotImplementedError("Couchbase client not enabled. Uncomment code to use.")

    async def upsert_document(self, keyspace: Keyspace, key: str, document: Dict[str, Any]) -> str:
        """
        Insert or update a document (upsert operation).

        Args:
            keyspace: Keyspace where to store document
            key: Document key
            document: Document data

        Returns:
            Document key
        """
        # Uncomment to enable Couchbase
        # collection = self.get_collection(keyspace)
        # collection.upsert(key, document)
        # return key
        raise NotImplementedError("Couchbase client not enabled. Uncomment code to use.")

    async def delete_document(self, keyspace: Keyspace, key: str) -> bool:
        """
        Delete a document by key.

        Args:
            keyspace: Keyspace where document is stored
            key: Document key

        Returns:
            True if document was deleted, False if not found
        """
        # Uncomment to enable Couchbase
        # try:
        #     collection = self.get_collection(keyspace)
        #     collection.remove(key)
        #     return True
        # except DocumentNotFoundException:
        #     return False
        raise NotImplementedError("Couchbase client not enabled. Uncomment code to use.")

    async def query_documents(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute a N1QL query and return results.

        Args:
            query: N1QL query string
            parameters: Query parameters

        Returns:
            List of result rows as dictionaries
        """
        # Uncomment to enable Couchbase
        # cluster = self.get_cluster()
        # options = QueryOptions()
        # if parameters:
        #     options = QueryOptions(**parameters)
        #
        # result = cluster.query(query, options)
        # return [row for row in result]
        raise NotImplementedError("Couchbase client not enabled. Uncomment code to use.")

    async def list_documents(self, keyspace: Keyspace, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        List all documents in a collection with optional limit.

        Args:
            keyspace: Keyspace to query
            limit: Maximum number of documents to return

        Returns:
            List of documents with their keys and data
        """
        # Uncomment to enable Couchbase
        # limit_clause = f" LIMIT {limit}" if limit is not None else ""
        # query = f"SELECT META().id, * FROM `{keyspace.bucket_name}`.`{keyspace.scope_name}`.`{keyspace.collection_name}`{limit_clause}"
        #
        # results = await self.query_documents(query)
        # return results
        raise NotImplementedError("Couchbase client not enabled. Uncomment code to use.")

    async def count_documents(self, keyspace: Keyspace) -> int:
        """
        Count documents in a collection.

        Args:
            keyspace: Keyspace to count

        Returns:
            Number of documents
        """
        # Uncomment to enable Couchbase
        # query = f"SELECT COUNT(*) as count FROM `{keyspace.bucket_name}`.`{keyspace.scope_name}`.`{keyspace.collection_name}`"
        # results = await self.query_documents(query)
        # return results[0]['count'] if results else 0
        raise NotImplementedError("Couchbase client not enabled. Uncomment code to use.")

    async def bulk_insert(self, keyspace: Keyspace, documents: List[Dict[str, Any]], keys: Optional[List[str]] = None) -> List[str]:
        """
        Insert multiple documents in bulk.

        Args:
            keyspace: Keyspace where to insert documents
            documents: List of document data dictionaries
            keys: List of keys (generates UUIDs if not provided)

        Returns:
            List of document keys
        """
        # Uncomment to enable Couchbase
        # if keys is None:
        #     keys = [str(uuid.uuid4()) for _ in documents]
        # elif len(keys) != len(documents):
        #     raise ValueError("Number of keys must match number of documents")
        #
        # collection = self.get_collection(keyspace)
        # for key, document in zip(keys, documents):
        #     collection.insert(key, document)
        #
        # return keys
        raise NotImplementedError("Couchbase client not enabled. Uncomment code to use.")

    async def health_check(self) -> bool:
        """
        Check if Couchbase connection is healthy.

        Returns:
            True if connection is healthy, False otherwise
        """
        # Uncomment to enable Couchbase
        # try:
        #     cluster = self.get_cluster()
        #     # Try to access the default bucket
        #     bucket = cluster.bucket(self._config.bucket)
        #     bucket.ping()
        #     return True
        # except Exception as e:
        #     logger.error(f"Health check failed: {e}")
        #     return False
        return False


# Global client instance
couchbase_client = CouchbaseClient()


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

async def get_couchbase_client() -> CouchbaseClient:
    """Get the global Couchbase client instance"""
    return couchbase_client


def create_keyspace(collection_name: str, scope_name: str = "_default", bucket_name: Optional[str] = None) -> Keyspace:
    """
    Helper function to create a keyspace.

    Args:
        collection_name: Name of the collection
        scope_name: Name of the scope (defaults to "_default")
        bucket_name: Name of the bucket (uses configured default if None)

    Returns:
        Keyspace instance
    """
    # For now, return a basic keyspace - will be functional when client is enabled
    return Keyspace(bucket_name or "default", scope_name, collection_name)


# Example usage function - remove in production
async def example_usage():
    """
    Example of how to use the Couchbase client.
    Remove this function when implementing your own logic.
    """
    # Initialize client (call during app startup)
    await couchbase_client.initialize()

    try:
        # Create a keyspace for users collection
        users_keyspace = couchbase_client.get_keyspace("users")

        # Insert a document
        user_data = {
            "name": "John Doe",
            "email": "john@example.com",
            "created_at": "2024-01-01T00:00:00Z"
        }
        user_id = await couchbase_client.insert_document(users_keyspace, user_data)

        # Get document by key
        user = await couchbase_client.get_document(users_keyspace, user_id)

        # Update document
        user_data["name"] = "John Smith"
        await couchbase_client.update_document(users_keyspace, user_id, user_data)

        # Query documents
        results = await couchbase_client.query_documents(
            f"SELECT * FROM `{users_keyspace}` WHERE email = $email",
            {"email": "john@example.com"}
        )

        # List all documents
        all_users = await couchbase_client.list_documents(users_keyspace, limit=10)

        # Bulk insert
        more_users = [
            {"name": "Alice", "email": "alice@example.com"},
            {"name": "Bob", "email": "bob@example.com"}
        ]
        await couchbase_client.bulk_insert(users_keyspace, more_users)

    finally:
        # Cleanup (call during app shutdown)
        await couchbase_client.close()
