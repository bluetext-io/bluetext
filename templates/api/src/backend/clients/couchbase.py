import uuid
import logging
from datetime import timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from couchbase.auth import PasswordAuthenticator
from couchbase.cluster import Cluster
from couchbase.options import ClusterOptions, QueryOptions
from couchbase.exceptions import DocumentNotFoundException, BucketNotFoundException
from couchbase.result import MutationResult

from ..conf import USE_COUCHBASE

logger = logging.getLogger(__name__)


@dataclass
class CouchbaseConf:
    """Couchbase configuration"""
    host: str
    port: int
    username: str
    password: str
    bucket: str
    protocol: str = "couchbase"
    
    def get_connection_url(self) -> str:
        """Get the connection URL for Couchbase"""
        return f"{self.protocol}://{self.host}:{self.port}"


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
    
    Only initializes if USE_COUCHBASE is True in configuration.
    """

    def __init__(self, config: Optional[CouchbaseConf] = None):
        self._cluster = None
        self._config = config
        self._initialized = False

    async def initialize(self):
        """Initialize the Couchbase client if enabled"""
        if not USE_COUCHBASE:
            logger.info("Couchbase disabled in configuration")
            return
            
        if not self._config:
            raise ValueError("CouchbaseConf required when USE_COUCHBASE is True")
            
        self._cluster = self._create_cluster()
        self._initialized = True
        logger.info("Couchbase client initialized")

    async def close(self):
        """Close the Couchbase client"""
        if self._cluster:
            self._cluster = None
            self._initialized = False
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

    def _ensure_initialized(self):
        """Ensure client is initialized"""
        if not USE_COUCHBASE:
            raise RuntimeError("Couchbase is disabled in configuration")
        if not self._initialized or not self._cluster:
            raise RuntimeError("Couchbase client not initialized")

    def get_cluster(self):
        """Get the cached cluster connection"""
        self._ensure_initialized()
        return self._cluster

    def get_keyspace(self, collection_name: str, scope_name: str = "_default", bucket_name: Optional[str] = None) -> Keyspace:
        """Create a Keyspace instance for database operations"""
        self._ensure_initialized()
        if bucket_name is None:
            bucket_name = self._config.bucket
        return Keyspace(bucket_name, scope_name, collection_name)

    def get_collection(self, keyspace: Keyspace):
        """Get a Couchbase Collection object from keyspace"""
        cluster = self.get_cluster()
        bucket = cluster.bucket(keyspace.bucket_name)
        scope = bucket.scope(keyspace.scope_name)
        return scope.collection(keyspace.collection_name)

    async def insert_document(self, keyspace: Keyspace, document: Dict[str, Any], key: Optional[str] = None) -> str:
        """Insert a document into a collection"""
        if key is None:
            key = str(uuid.uuid4())

        collection = self.get_collection(keyspace)
        collection.insert(key, document)
        return key

    async def get_document(self, keyspace: Keyspace, key: str) -> Optional[Dict[str, Any]]:
        """Get a document by key"""
        try:
            collection = self.get_collection(keyspace)
            result = collection.get(key)
            return result.content_as[dict]
        except DocumentNotFoundException:
            return None

    async def update_document(self, keyspace: Keyspace, key: str, document: Dict[str, Any]) -> bool:
        """Update a document by key"""
        try:
            collection = self.get_collection(keyspace)
            collection.replace(key, document)
            return True
        except DocumentNotFoundException:
            return False

    async def upsert_document(self, keyspace: Keyspace, key: str, document: Dict[str, Any]) -> str:
        """Insert or update a document (upsert operation)"""
        collection = self.get_collection(keyspace)
        collection.upsert(key, document)
        return key

    async def delete_document(self, keyspace: Keyspace, key: str) -> bool:
        """Delete a document by key"""
        try:
            collection = self.get_collection(keyspace)
            collection.remove(key)
            return True
        except DocumentNotFoundException:
            return False

    async def query_documents(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute a N1QL query and return results"""
        cluster = self.get_cluster()
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

    async def bulk_insert(self, keyspace: Keyspace, documents: List[Dict[str, Any]], keys: Optional[List[str]] = None) -> List[str]:
        """Insert multiple documents in bulk"""
        if keys is None:
            keys = [str(uuid.uuid4()) for _ in documents]
        elif len(keys) != len(documents):
            raise ValueError("Number of keys must match number of documents")

        collection = self.get_collection(keyspace)
        for key, document in zip(keys, documents):
            collection.insert(key, document)

        return keys

    async def health_check(self) -> bool:
        """Check if Couchbase connection is healthy"""
        if not USE_COUCHBASE:
            return False
            
        try:
            cluster = self.get_cluster()
            bucket = cluster.bucket(self._config.bucket)
            bucket.ping()
            return True
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False