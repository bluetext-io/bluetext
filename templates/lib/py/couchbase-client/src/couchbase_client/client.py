import uuid
import logging
import asyncio
import time
from datetime import timedelta
from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass

from couchbase.auth import PasswordAuthenticator
from couchbase.cluster import Cluster
from couchbase.options import ClusterOptions, QueryOptions
from couchbase.exceptions import (
    DocumentNotFoundException,
    BucketNotFoundException,
    BucketAlreadyExistsException,
    ScopeNotFoundException,
    ScopeAlreadyExistsException,
    CollectionAlreadyExistsException,
    CollectionNotFoundException
)
from couchbase.result import MutationResult
from couchbase.management.buckets import CreateBucketSettings, BucketType

logger = logging.getLogger(__name__)


@dataclass
class CouchbaseConf:
    """Couchbase configuration"""
    host: str
    username: str
    password: str
    bucket: str
    protocol: str = "couchbase"

    def get_connection_url(self) -> str:
        """Get the connection URL for Couchbase"""
        return f"{self.protocol}://{self.host}/{self.bucket}"


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
    Clean Couchbase client for basic operations.
    """

    def __init__(self, config: CouchbaseConf, auto_create: bool = True):
        self._cluster = None
        self._config = config
        self._connected = False
        self._connection_task = None
        self._last_connection_error = None
        self._last_error_log_time = 0
        self._auto_create = auto_create

    async def init_connection(self):
        """Initialize connection with retry loop - call in background task"""
        self._connection_task = asyncio.create_task(self._connection_retry_loop())

    async def _connection_retry_loop(self):
        """Retry connection loop that runs in background"""
        while not self._connected:
            try:
                self._cluster = self._create_cluster()
                self._connected = True
                logger.info("Couchbase connection established successfully")
                break
            except Exception as e:
                self._last_connection_error = str(e)
                current_time = time.time()

                # Log error every 10 seconds
                if current_time - self._last_error_log_time >= 10:
                    logger.warning(f"Couchbase connection failed, retrying: {e}")
                    self._last_error_log_time = current_time

                await asyncio.sleep(1)  # Wait 1 second before retry

    async def close(self):
        """Close the Couchbase client"""
        if self._cluster:
            self._cluster = None
            logger.info("Couchbase client closed")

    def _create_cluster(self):
        """Create and cache cluster connection"""
        auth = PasswordAuthenticator(self._config.username, self._config.password)

        cluster_options = ClusterOptions(auth)
        if self._config.protocol == "couchbases":
            cluster_options.verify_credentials = True

        cluster = Cluster(self._config.get_connection_url(), cluster_options)
        cluster.wait_until_ready(timedelta(seconds=30))

        return cluster

    async def _await_connected(self):
        """Ensure client is connected (blocks until connected)"""
        while not self._connected:
            await asyncio.sleep(0.1)  # Wait for connection

    async def get_cluster(self):
        """Get the cached cluster connection"""
        await self._await_connected()
        return self._cluster

    def get_keyspace(
        self,
        collection_name: str,
        scope_name: str = "_default",
        bucket_name: Optional[str] = None
    ) -> Keyspace:
        """Create a Keyspace instance for database operations"""
        if bucket_name is None:
            bucket_name = self._config.bucket
        return Keyspace(bucket_name, scope_name, collection_name)

    async def get_collection(self, keyspace: Keyspace):
        """Get a Couchbase Collection object from keyspace - auto-create if auto_create is True"""
        cluster = await self.get_cluster()

        if self._auto_create:
            await self._ensure_bucket_exists(keyspace.bucket_name)
            await self._ensure_scope_exists(keyspace.bucket_name, keyspace.scope_name)
            await self._ensure_collection_exists(keyspace)

        bucket = cluster.bucket(keyspace.bucket_name)
        
        # Wait for bucket to be ready before accessing scope
        try:
            await bucket.on_connect()
        except AttributeError:
            # Older SDK versions may not have on_connect, continue anyway
            pass

        scope = bucket.scope(keyspace.scope_name)

        return scope.collection(keyspace.collection_name)


    async def insert_document(self, keyspace: Keyspace, document: Dict[str, Any], key: Optional[str] = None) -> str:
        """Insert a document into a collection"""
        if key is None:
            key = str(uuid.uuid4())

        # Auto-serialize Pydantic models
        if hasattr(document, 'model_dump'):
            document = document.model_dump(mode='json')

        collection = await self.get_collection(keyspace)
        collection.insert(key, document)
        return key

    async def get_document(self, keyspace: Keyspace, key: str) -> Optional[Dict[str, Any]]:
        """Get a document by key"""
        try:
            collection = await self.get_collection(keyspace)
            result = collection.get(key)
            return result.content_as[dict]
        except DocumentNotFoundException:
            return None

    async def update_document(self, keyspace: Keyspace, key: str, document: Dict[str, Any]) -> bool:
        """Update a document by key"""
        try:
            collection = await self.get_collection(keyspace)
            collection.replace(key, document)
            return True
        except DocumentNotFoundException:
            return False

    async def upsert_document(self, keyspace: Keyspace, key: str, document: Dict[str, Any]) -> str:
        """Insert or update a document (upsert operation)"""
        # Auto-serialize Pydantic models
        if hasattr(document, 'model_dump'):
            document = document.model_dump(mode='json')

        collection = await self.get_collection(keyspace)
        collection.upsert(key, document)
        return key

    async def delete_document(self, keyspace: Keyspace, key: str) -> bool:
        """Delete a document by key"""
        try:
            collection = await self.get_collection(keyspace)
            collection.remove(key)
            return True
        except DocumentNotFoundException:
            return False

    async def query_documents(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute a N1QL query and return results"""
        cluster = await self.get_cluster()
        options = QueryOptions()
        if parameters:
            options = QueryOptions(**parameters)

        result = cluster.query(query, options)
        return [row for row in result]

    async def list_documents(self, keyspace: Keyspace, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """List all documents in a collection with optional limit"""
        limit_clause = f" LIMIT {limit}" if limit is not None else ""
        query = f"SELECT META().id, * FROM `{keyspace.bucket_name}`.`{keyspace.scope_name}`.`{keyspace.collection_name}`{limit_clause}"

        results = await self.query_documents(query)
        return results

    async def count_documents(self, keyspace: Keyspace) -> int:
        """Count documents in a collection"""
        query = f"SELECT COUNT(*) as count FROM `{keyspace.bucket_name}`.`{keyspace.scope_name}`.`{keyspace.collection_name}`"
        results = await self.query_documents(query)
        return results[0]['count'] if results else 0

    # N1QL Query Helpers - Use these to avoid common query mistakes
    #
    # Example usage:
    #   # List users with pagination
    #   keyspace = client.get_keyspace("users")
    #   query = client.build_list_query(keyspace, limit=50, offset=0)
    #   results = await client.query_documents(query)
    #
    #   # Search users by name/email
    #   query, params = client.build_search_query(keyspace, ["name", "email"], "john")
    #   results = await client.query_documents(query, params)
    #
    #   # Filter active users
    #   query = client.build_filter_query(keyspace, "u.is_active = true", limit=100)
    #   results = await client.query_documents(query)

    def build_list_query(self, keyspace: Keyspace, limit: int = 100, offset: int = 0,
                        order_by: str = "created_at DESC") -> str:
        """Build standardized list query with proper ID handling"""
        collection_alias = keyspace.collection_name[0]  # Use first letter as alias
        return f"""
            SELECT META().id as id, {collection_alias}.*
            FROM `{keyspace.bucket_name}`.`{keyspace.scope_name}`.`{keyspace.collection_name}` {collection_alias}
            ORDER BY {collection_alias}.{order_by}
            LIMIT {limit} OFFSET {offset}
        """

    def build_filter_query(self, keyspace: Keyspace, where_clause: str,
                          order_by: str = "created_at DESC", limit: Optional[int] = None) -> str:
        """Build standardized filter query with proper ID handling"""
        collection_alias = keyspace.collection_name[0]  # Use first letter as alias
        limit_clause = f" LIMIT {limit}" if limit else ""
        return f"""
            SELECT META().id as id, {collection_alias}.*
            FROM `{keyspace.bucket_name}`.`{keyspace.scope_name}`.`{keyspace.collection_name}` {collection_alias}
            WHERE {where_clause}
            ORDER BY {collection_alias}.{order_by}{limit_clause}
        """

    def build_search_query(self, keyspace: Keyspace, search_fields: List[str],
                          search_term: str, limit: int = 10) -> tuple[str, Dict[str, Any]]:
        """Build standardized search query with proper ID handling"""
        collection_alias = keyspace.collection_name[0]  # Use first letter as alias

        # Build LIKE conditions for each field
        conditions = []
        for field in search_fields:
            conditions.append(f"LOWER({collection_alias}.{field}) LIKE LOWER($search)")

        where_clause = " OR ".join(conditions)

        query = f"""
            SELECT META().id as id, {collection_alias}.*
            FROM `{keyspace.bucket_name}`.`{keyspace.scope_name}`.`{keyspace.collection_name}` {collection_alias}
            WHERE {where_clause}
            ORDER BY {collection_alias}.created_at DESC
            LIMIT {limit}
        """

        search_pattern = f"%{search_term}%"
        parameters = {"search": search_pattern}

        return query, parameters

    async def _ensure_bucket_exists(self, bucket_name: str):
        """Ensure a bucket exists, create it if it doesn't"""
        cluster = await self.get_cluster()
        bucket_manager = cluster.buckets()

        try:
            # Check if bucket exists
            bucket_manager.get_bucket(bucket_name)
            logger.debug(f"Bucket '{bucket_name}' already exists")
        except BucketNotFoundException:
            # Bucket doesn't exist - create it
            logger.info(f"Auto-creating bucket: {bucket_name}")
            try:
                settings = CreateBucketSettings(
                    name=bucket_name,
                    bucket_type=BucketType.COUCHBASE,
                    ram_quota_mb=256  # Default RAM quota, adjust as needed
                )
                bucket_manager.create_bucket(settings)
                logger.info(f"Successfully created bucket: {bucket_name}")
                # Wait a moment for bucket to be ready
                await asyncio.sleep(2)
            except BucketAlreadyExistsException:
                # Race condition - another process created it
                logger.info(f"Bucket already exists (race condition): {bucket_name}")
            except Exception as e:
                logger.error(f"Failed to create bucket {bucket_name}: {e}")
                raise

    async def _ensure_scope_exists(self, bucket_name: str, scope_name: str):
        """Ensure a scope exists, create it if it doesn't"""
        if scope_name == "_default":
            # Default scope always exists
            return

        cluster = await self.get_cluster()
        bucket = cluster.bucket(bucket_name)
        collection_manager = bucket.collections()

        try:
            # Get all scopes to check if our scope exists
            scopes = collection_manager.get_all_scopes()
            scope_exists = any(scope.name == scope_name for scope in scopes)

            if not scope_exists:
                logger.info(f"Auto-creating scope: {scope_name} in bucket: {bucket_name}")
                try:
                    collection_manager.create_scope(scope_name)
                    logger.info(f"Successfully created scope: {scope_name}")
                    # Wait a moment for scope to be ready
                    await asyncio.sleep(1)
                except ScopeAlreadyExistsException:
                    # Race condition - another process created it
                    logger.info(f"Scope already exists (race condition): {scope_name}")
                except Exception as e:
                    logger.error(f"Failed to create scope {scope_name}: {e}")
                    raise
            else:
                logger.debug(f"Scope '{scope_name}' already exists in bucket '{bucket_name}'")
        except Exception as e:
            logger.error(f"Failed to check/create scope {scope_name}: {e}")
            raise


    async def _ensure_collection_exists(self, keyspace: Keyspace) -> bool:
        """Helper method to create a collection if it doesn't exist"""
        cluster = await self.get_cluster()
        bucket = cluster.bucket(keyspace.bucket_name)
        collection_manager = bucket.collections()

        try:
            collection_manager.create_collection(
                scope_name=keyspace.scope_name,
                collection_name=keyspace.collection_name
            )
            logger.info(f"Successfully created collection: {keyspace}")
            return True
        except CollectionAlreadyExistsException:
            return False
        except Exception as e:
            logger.error(f"Failed to create collection {keyspace}: {e}")
            raise

    def health_check(self) -> Dict[str, Any]:
        """Check if Couchbase connection is healthy (non-blocking for health endpoints)"""
        if not self._connected:
            return {
                "connected": False,
                "status": "connecting",
                "last_error": self._last_connection_error
            }

        return {"connected": True, "status": "healthy"}
