import os
import time
import urllib.request
import urllib.error
import urllib.parse
from typing import Dict, Any
from pathlib import Path
from couchbase.auth import PasswordAuthenticator
from couchbase.cluster import Cluster
from couchbase.options import ClusterOptions, WaitUntilReadyOptions
from couchbase.exceptions import (
    RequestCanceledException,
    AuthenticationException,
    BucketAlreadyExistsException,
    ScopeAlreadyExistsException,
    CollectionAlreadyExistsException,
    BucketNotFoundException,
    BucketDoesNotExistException,
    ScopeNotFoundException,
    CollectionNotFoundException
)
from couchbase.diagnostics import ServiceType
from couchbase.management.buckets import CreateBucketSettings, BucketType
from couchbase.management.collections import CollectionSpec
from datetime import timedelta
from config import Config
from utils.logger import get_logger

class CouchbaseController:
    """Controls Couchbase bucket, scope, and collection operations."""

    def __init__(self, environment: str, config: Config = None, host: str = None, username: str = None, password: str = None, tls: bool = None):
        self.environment = environment
        self.config = config
        self.logger = get_logger(f'couchbase-controller')

        # Load from environment variables if not provided
        self.host = host or self._get_env_var('COUCHBASE_HOST', 'couchbase')
        self.username = username or self._get_env_var('COUCHBASE_USERNAME', 'user')
        self.password = password or self._get_env_var('COUCHBASE_PASSWORD', 'password')
        self.tls = tls if tls is not None else self._get_env_var('COUCHBASE_TLS', 'false').lower() == 'true'
        self.couchbase_type = self._get_env_var('COUCHBASE_TYPE', 'server')
        self.cluster = None
        
        self.logger.info(f"🔧 Initializing Couchbase controller for environment: {environment}")
        self.logger.info(f"📡 Connection: {self.host} (TLS: {self.tls}, Type: {self.couchbase_type})")

    def _get_env_var(self, name: str, default: str = None) -> str:
        """Get environment variable with optional default."""
        try:
            if default is not None:
                return os.environ.get(name, default)
            else:
                return os.environ[name]
        except KeyError:
            raise KeyError(f"Environment variable '{name}' is not set")

    def get_connection_string(self) -> str:
        """Get the connection string for Couchbase."""
        protocol = "couchbases" if self.tls else "couchbase"
        return f"{protocol}://{self.host}"

    def _test_connection(self) -> bool:
        """Test basic connectivity to Couchbase server."""
        import base64
        protocol = "https" if self.tls else "http"
        port = "18091" if self.tls else "8091"
        test_url = f"{protocol}://{self.host}:{port}/pools"

        try:
            # First try without auth (for uninitialized clusters)
            request = urllib.request.Request(test_url, method='GET')
            with urllib.request.urlopen(request, timeout=10) as response:
                self.logger.debug(f"✅ Connection test successful (no auth): {response.code}")
                return True
        except urllib.error.HTTPError as e:
            if e.code == 401:
                # Cluster is initialized, try with auth
                try:
                    credentials = base64.b64encode(f'{self.username}:{self.password}'.encode()).decode('ascii')
                    request = urllib.request.Request(test_url, method='GET')
                    request.add_header('Authorization', f'Basic {credentials}')
                    with urllib.request.urlopen(request, timeout=10) as response:
                        self.logger.debug(f"✅ Connection test successful (with auth): {response.code}")
                        return True
                except Exception as auth_e:
                    self.logger.debug(f"❌ Connection test failed with auth: {auth_e}")
                    return False
            else:
                self.logger.debug(f"❌ Connection test failed: HTTP {e.code}")
                return False
        except Exception as e:
            self.logger.debug(f"❌ Connection test failed: {e}")
            return False

    def _get_cluster_init_params(self) -> Dict[str, Any]:
        """Get parameters for cluster initialization."""
        protocol = "https" if self.tls else "http"
        port = "18091" if self.tls else "8091"
        return {
            'url': f"{protocol}://{self.host}:{port}/clusterInit",
            'data': {
                'username': self.username,
                'password': self.password,
                'services': 'kv,n1ql,index,fts,eventing',
                'hostname': '127.0.0.1',
                'memoryQuota': '256',
                'sendStats': 'false',
                'clusterName': 'cillers',
                'setDefaultMemQuotas': 'true',
                'indexerStorageMode': 'plasma',
                'port': 'SAME'
            }
        }

    def ensure_initialized(self) -> None:
        """Ensure the Couchbase cluster is initialized."""
        import base64
        self.logger.info("🔄 Ensuring Couchbase cluster is initialized...")

        # First check if cluster is already initialized
        protocol = "https" if self.tls else "http"
        port = "18091" if self.tls else "8091"
        check_url = f"{protocol}://{self.host}:{port}/pools/default"

        # Check with authentication
        try:
            credentials = base64.b64encode(f'{self.username}:{self.password}'.encode()).decode('ascii')
            request = urllib.request.Request(check_url, method='GET')
            request.add_header('Authorization', f'Basic {credentials}')
            with urllib.request.urlopen(request, timeout=10) as response:
                self.logger.info("✅ Cluster already initialized and accessible with provided credentials")
                return
        except urllib.error.HTTPError as e:
            if e.code != 404:  # 404 means not initialized, anything else is an error
                self.logger.debug(f"Cluster check returned HTTP {e.code}")
        except Exception:
            pass  # Try initialization

        params = self._get_cluster_init_params()
        encoded_data = urllib.parse.urlencode(params['data']).encode()
        request = urllib.request.Request(
            params['url'],
            data=encoded_data,
            method='POST'
        )

        max_retries = 30  # Reduced from 100 to fail faster
        for attempt in range(max_retries):
            try:
                with urllib.request.urlopen(request, timeout=30) as response:  # Reduced timeout from 10 minutes
                    response_text = response.read().decode()
                    self.logger.info("✅ Cluster initialization successful")
                    return
            except urllib.error.HTTPError as e:
                error_body = e.read().decode() if hasattr(e, 'read') else str(e)
                self.logger.debug(f"HTTP Error {e.code}: {error_body}")

                if e.code == 400 and ('already initialized' in error_body or 'Cluster is already initialized' in error_body):
                    self.logger.info("✅ Cluster already initialized")
                    return
                elif e.code == 401:
                    # 401 on /clusterInit endpoint means cluster is already initialized
                    self.logger.info("✅ Cluster already initialized (401 on init endpoint)")
                    return
                elif attempt == max_retries - 1:
                    self.logger.error(f'❌ HTTP Error after {max_retries} attempts: {e.code} - {error_body}')
                    raise e
                    
            except urllib.error.URLError as e:
                if attempt == max_retries - 1:
                    self.logger.error(f'❌ Connection failed after {max_retries} attempts: {e}')
                    raise e
                self.logger.debug(f"⏳ Connection failed, retrying... (attempt {attempt + 1}/{max_retries}): {e}")
                
            except Exception as e:
                if attempt == max_retries - 1:
                    self.logger.error(f'❌ Unexpected error after {max_retries} attempts: {e}')
                    raise e
                self.logger.debug(f"⏳ Unexpected error, retrying... (attempt {attempt + 1}/{max_retries}): {e}")
                
            # Brief wait before retry
            time.sleep(2)

        raise Exception("Failed to initialize cluster after maximum retries")

    def _is_connection_valid(self, cluster: Cluster) -> bool:
        """Validate if the cluster connection is still active."""
        try:
            # Use ping to verify connectivity
            result = cluster.ping()
            # Check if at least one service is responding
            for endpoint, reports in result.endpoints.items():
                for report in reports:
                    if report.state.name == 'OK':
                        return True
            return False
        except Exception as e:
            self.logger.debug(f"Connection validation failed: {e}")
            return False

    def connect(self) -> Cluster:
        """Connect to Couchbase cluster."""
        # Validate existing connection
        if self.cluster is not None:
            if self._is_connection_valid(self.cluster):
                self.logger.debug("✅ Using existing valid connection")
                return self.cluster
            else:
                self.logger.info("🔄 Cached connection invalid, reconnecting...")
                self.cluster = None  # Clear invalid connection

        auth = PasswordAuthenticator(self.username, self.password)
        cluster_options = ClusterOptions(auth)

        if self.tls:
            cluster_options.verify_credentials = True

        self.cluster = Cluster(self.get_connection_string(), cluster_options)

        # Wait for cluster to be ready
        wait_options = WaitUntilReadyOptions(
            service_types=[ServiceType.KeyValue, ServiceType.Query, ServiceType.Management]
        )
        self.cluster.wait_until_ready(timedelta(seconds=300), wait_options)

        return self.cluster

    def connect_with_retry(self, max_retries: int = 30, retry_interval: int = 2) -> Cluster:
        """Connect to Couchbase with retry logic."""
        for attempt in range(max_retries):
            try:
                return self.connect()
            except (RequestCanceledException, AuthenticationException) as e:
                if attempt == max_retries - 1:
                    if isinstance(e, RequestCanceledException):
                        print('Timeout: Connecting to Couchbase cluster.')
                    elif isinstance(e, AuthenticationException):
                        print('Authentication failed: Couchbase cluster might not be fully initialized.')
                    raise e

                if isinstance(e, RequestCanceledException):
                    print("Waiting for connection to Couchbase cluster...")
                elif isinstance(e, AuthenticationException):
                    print("Waiting for Couchbase cluster to initialize...")

                time.sleep(retry_interval)

        raise Exception("Failed to connect to Couchbase after maximum retries")

    def _wait_for_bucket_ready(self, cluster: Cluster, bucket_name: str, max_retries: int = 30, retry_interval: int = 2) -> None:
        """Wait for a bucket to be ready by attempting to access it."""
        for attempt in range(max_retries):
            try:
                # Try to access the bucket and perform a basic operation
                bucket = cluster.bucket(bucket_name)
                # Try to get collection manager to verify bucket is accessible
                collection_manager = bucket.collections()
                collection_manager.get_all_scopes()
                self.logger.info(f"✅ Bucket '{bucket_name}' is ready")
                return
            except Exception as e:
                if attempt == max_retries - 1:
                    print(f"Bucket '{bucket_name}' failed to become ready after {max_retries} attempts: {e}")
                    raise e

                self.logger.debug(f"⏳ Bucket '{bucket_name}' not ready yet, waiting... (attempt {attempt + 1}/{max_retries})")
                time.sleep(retry_interval)

        raise Exception(f"Bucket '{bucket_name}' failed to become ready after maximum retries")

    def _wait_for_scope_ready(self, collection_manager, scope_name: str, max_retries: int = 10, retry_interval: int = 1) -> None:
        """Wait for a scope to be ready by checking if it appears in the scopes list."""
        for attempt in range(max_retries):
            try:
                all_scopes = collection_manager.get_all_scopes()
                scope_exists = any(scope.name == scope_name for scope in all_scopes)
                if scope_exists:
                    print(f"Scope '{scope_name}' is ready")
                    return
                else:
                    if attempt == max_retries - 1:
                        raise Exception(f"Scope '{scope_name}' not found after creation")
                    print(f"Scope '{scope_name}' not ready yet, waiting... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(retry_interval)
            except Exception as e:
                if attempt == max_retries - 1:
                    print(f"Scope '{scope_name}' failed to become ready after {max_retries} attempts: {e}")
                    raise e
                print(f"Scope '{scope_name}' not ready yet, waiting... (attempt {attempt + 1}/{max_retries})")
                time.sleep(retry_interval)

        raise Exception(f"Scope '{scope_name}' failed to become ready after maximum retries")

    def ensure_bucket(self, bucket_name: str, settings: Dict[str, Any]) -> None:
        """Ensure a bucket exists with the specified settings."""
        cluster = self.connect_with_retry()
        bucket_manager = cluster.buckets()

        try:
            # Check if bucket exists
            bucket_manager.get_bucket(bucket_name)
            self.logger.info(f"✅ Bucket '{bucket_name}' already exists")
            return
        except (BucketNotFoundException, BucketDoesNotExistException):
            # Create bucket
            self.logger.info(f"🔄 Creating bucket '{bucket_name}'...")

        # Create bucket logic
        bucket_type = BucketType.COUCHBASE
        if settings.get('bucket_type') == 'ephemeral':
            bucket_type = BucketType.EPHEMERAL
        elif settings.get('bucket_type') == 'memcached':
            bucket_type = BucketType.MEMCACHED

        # Build create settings, only including non-None values
        create_settings_kwargs = {
            'name': bucket_name,
            'bucket_type': bucket_type,
            'ram_quota_mb': settings.get('ram_quota_mb', 100),
            'num_replicas': settings.get('num_replicas', 0),
            'flush_enabled': settings.get('flush_enabled', False)
        }

        # Only add max_ttl if it's greater than 0
        max_ttl_seconds = settings.get('max_ttl', 0)
        if max_ttl_seconds and max_ttl_seconds > 0:
            create_settings_kwargs['max_ttl'] = timedelta(seconds=max_ttl_seconds)

        create_settings = CreateBucketSettings(**create_settings_kwargs)

        try:
            bucket_manager.create_bucket(create_settings)
            self.logger.info(f"✅ Bucket '{bucket_name}' created successfully")
            # Wait for bucket to be ready after creation
            self.logger.info(f"⏳ Waiting for bucket '{bucket_name}' to be ready...")
            self._wait_for_bucket_ready(cluster, bucket_name)
        except BucketAlreadyExistsException:
            self.logger.info(f"✅ Bucket '{bucket_name}' already exists")

    def ensure_scope(self, bucket_name: str, scope_name: str) -> None:
        """Ensure a scope exists in the specified bucket. Assumes bucket already exists and is ready."""
        # Skip _default scope as it exists by default and cannot be created
        if scope_name == '_default':
            print(f"Scope '_default' exists by default in bucket '{bucket_name}'")
            return

        cluster = self.connect_with_retry()
        bucket = cluster.bucket(bucket_name)
        collection_manager = bucket.collections()

        # Check if scope exists by getting all scopes
        all_scopes = collection_manager.get_all_scopes()
        scope_exists = any(scope.name == scope_name for scope in all_scopes)

        if scope_exists:
            print(f"Scope '{scope_name}' already exists in bucket '{bucket_name}'")
            return

        # Create scope
        print(f"Creating scope '{scope_name}' in bucket '{bucket_name}'...")
        try:
            collection_manager.create_scope(scope_name)
            print(f"Scope '{scope_name}' created successfully")
            # Wait for scope to be fully ready
            self._wait_for_scope_ready(collection_manager, scope_name)
        except ScopeAlreadyExistsException:
            print(f"Scope '{scope_name}' already exists")

    def ensure_collection(self, bucket_name: str, scope_name: str, 
                         collection_name: str, settings: Dict[str, Any]) -> None:
        """Ensure a collection exists in the specified scope. Assumes bucket and scope already exist and are ready."""
        # Skip _default collection in _default scope as it exists by default and cannot be created
        if scope_name == '_default' and collection_name == '_default':
            print(f"Collection '_default' exists by default in scope '_default'")
            return

        cluster = self.connect_with_retry()
        bucket = cluster.bucket(bucket_name)
        collection_manager = bucket.collections()

        # Check if collection exists by getting all scopes
        all_scopes = collection_manager.get_all_scopes()
        target_scope = None

        for scope in all_scopes:
            if scope.name == scope_name:
                target_scope = scope
                break

        if target_scope is None:
            raise ScopeNotFoundException(f"Scope '{scope_name}' not found in bucket '{bucket_name}'")

        # Check if collection exists in the scope
        collection_exists = any(c.name == collection_name for c in target_scope.collections)

        if collection_exists:
            print(f"Collection '{collection_name}' already exists in scope '{scope_name}'")
            return

        # Create collection
        print(f"Creating collection '{collection_name}' in scope '{scope_name}'...")

        max_ttl = settings.get('max_ttl', 0)

        try:
            # Use the newer API signature without CollectionSpec
            if max_ttl and max_ttl > 0:
                collection_manager.create_collection(
                    scope_name,
                    collection_name,
                    max_expiry=timedelta(seconds=max_ttl)
                )
            else:
                collection_manager.create_collection(
                    scope_name,
                    collection_name
                )
            print(f"Collection '{collection_name}' created successfully")
        except CollectionAlreadyExistsException:
            print(f"Collection '{collection_name}' already exists")

    def _load_couchbase_config(self) -> Dict[str, Any]:
        """Load Couchbase configuration from YAML file using the config object."""
        if self.config is None:
            raise ValueError("Config object is required but not provided")
        return self.config.load_target_config('couchbase')

    def _merge_settings(self, global_defaults: Dict[str, Any], 
                       item_defaults: Dict[str, Any], 
                       env_settings: Dict[str, Any]) -> Dict[str, Any]:
        """Merge settings with precedence: env_settings > item_defaults > global_defaults."""
        result = {}

        # Start with global defaults
        if global_defaults:
            result.update(global_defaults)

        # Apply item defaults
        if item_defaults:
            result.update(item_defaults)

        # Apply environment-specific settings
        if env_settings:
            result.update(env_settings)

        return result

    def _get_bucket_settings(self, bucket_name: str, bucket_config: Dict[str, Any], 
                            couchbase_config: Dict[str, Any], environment: str) -> Dict[str, Any]:
        """Get merged settings for a bucket."""
        global_defaults = couchbase_config.get('bucket_defaults', {})
        item_defaults = bucket_config.get('defaults', {})
        env_settings = bucket_config.get('env_settings', {}).get(environment, {})

        return self._merge_settings(global_defaults, item_defaults, env_settings)

    def _get_collection_settings(self, collection_config: Dict[str, Any], 
                                couchbase_config: Dict[str, Any], environment: str) -> Dict[str, Any]:
        """Get merged settings for a collection."""
        global_defaults = couchbase_config.get('collection_defaults', {})
        item_defaults = collection_config.get('defaults', {})
        env_settings = collection_config.get('env_settings', {}).get(environment, {})

        return self._merge_settings(global_defaults, item_defaults, env_settings)

    def run_ops(self) -> None:
        """Run all Couchbase operations for the configured environment."""
        self.logger.info("🔄 Processing Couchbase resources...")

        # Test basic connectivity first
        self.logger.info("🔍 Testing connection to Couchbase server...")
        max_connection_retries = 30
        for attempt in range(max_connection_retries):
            if self._test_connection():
                break
            if attempt == max_connection_retries - 1:
                raise Exception(f"Failed to connect to Couchbase server at {self.host} after {max_connection_retries} attempts")
            self.logger.debug(f"⏳ Connection test failed, retrying... (attempt {attempt + 1}/{max_connection_retries})")
            time.sleep(2)

        # Only initialize cluster if it's a server type (not client)
        if self.couchbase_type == 'server':
            self.ensure_initialized()

        # Connect to cluster and verify it's ready
        cluster = self.connect_with_retry()
        self.logger.info("✅ Couchbase cluster is ready and initialized")

        # Load configuration and ensure resources
        couchbase_config = self._load_couchbase_config()
        self._ensure_resources(couchbase_config)
        self.logger.info("🎉 Couchbase resources processed successfully")

    def _ensure_resources(self, couchbase_config: Dict[str, Any]) -> None:
        """Ensure all Couchbase resources exist according to configuration."""
        buckets = couchbase_config.get('buckets', {})

        for bucket_name, bucket_config in buckets.items():
            self.logger.info(f"🪣 Processing bucket: {bucket_name}")

            # Get bucket settings
            bucket_settings = self._get_bucket_settings(bucket_name, bucket_config, couchbase_config, self.environment)

            # Ensure bucket exists
            self.ensure_bucket(bucket_name, bucket_settings)

            # Process scopes
            scopes = bucket_config.get('scopes', {})
            for scope_name, scope_config in scopes.items():
                self.logger.info(f"📂 Processing scope: {scope_name}")

                # Ensure scope exists
                self.ensure_scope(bucket_name, scope_name)

                # Process collections
                collections = scope_config.get('collections', {})
                for collection_name, collection_config in collections.items():
                    self.logger.info(f"📄 Processing collection: {collection_name}")

                    # Get collection settings
                    collection_settings = self._get_collection_settings(collection_config, couchbase_config, self.environment)

                    # Small delay to ensure scope is fully propagated before creating collections
                    time.sleep(0.5)

                    # Ensure collection exists
                    self.ensure_collection(bucket_name, scope_name, collection_name, collection_settings)