import asyncio
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Optional, List, Any, Dict

from temporalio.client import Client, TLSConfig
from temporalio.contrib.pydantic import pydantic_data_converter
from temporalio.worker import Worker

logger = logging.getLogger(__name__)


@dataclass
class TemporalConf:
    """Temporal configuration"""
    host: str
    port: int
    namespace: str
    task_queue: str

    def get_target_host(self) -> str:
        """Get Temporal server target host"""
        return f"{self.host}:{self.port}"


class TemporalClient:
    """
    Enhanced Temporal client wrapper that handles connection retry and worker management.
    """

    def __init__(
        self,
        config: TemporalConf,
        workflows: Optional[List[Any]] = None,
        activities: Optional[List[Any]] = None,
        tls: Optional[TLSConfig] = None,
        use_pydantic: bool = True,
    ):
        """
        Initialize the enhanced Temporal client.

        Args:
            config: Temporal configuration
            workflows: List of workflow classes to register
            activities: List of activity functions to register
            tls: Optional TLS configuration
            use_pydantic: Whether to use pydantic_data_converter (default: True)
        """
        self._config = config
        self._workflows = workflows or []
        self._activities = activities or []
        self._tls = tls
        self._use_pydantic = use_pydantic
        self._client: Optional[Client] = None
        self._worker: Optional[Worker] = None
        self._connected = False
        self._worker_task = None
        self._connection_task = None
        self._last_connection_error = None
        self._last_error_log_time = 0
        self._activity_executor = ThreadPoolExecutor(
            max_workers=4,
            thread_name_prefix="temporal-activity"
        )

    async def initialize(self):
        """Initialize client and start connection retry loop in background"""
        logger.info("Temporal client initialized")
        self._connection_task = asyncio.create_task(self._connection_retry_loop())

    async def _connection_retry_loop(self):
        """Retry connection loop that runs in background"""
        first_attempt = True
        while not self._connected:
            try:
                current_time = time.time()

                # Log connection attempt on first try or every 10 seconds
                if first_attempt or current_time - self._last_error_log_time >= 10:
                    logger.info(
                        f"Connecting to Temporal server at {self._config.get_target_host()}"
                    )
                    self._last_error_log_time = current_time
                    first_attempt = False

                # Connect with optional pydantic data converter
                connect_kwargs = {
                    "target_host": self._config.get_target_host(),
                    "namespace": self._config.namespace,
                    "tls": self._tls,
                }

                if self._use_pydantic:
                    connect_kwargs["data_converter"] = pydantic_data_converter

                self._client = await Client.connect(**connect_kwargs)

                logger.info("Connected to Temporal server")

                # Initialize and start worker
                await self._init_worker()

                self._connected = True
                logger.info("Temporal connection established successfully")
                break

            except Exception as e:
                self._last_connection_error = str(e)
                current_time = time.time()

                # Log error every 10 seconds
                if current_time - self._last_error_log_time >= 10:
                    logger.warning(f"Temporal connection failed, retrying: {e}")
                    self._last_error_log_time = current_time

                await asyncio.sleep(1)  # Wait 1 second before retry

    async def _init_worker(self):
        """Initialize and start Temporal worker"""
        if not self._workflows and not self._activities:
            logger.info(
                "No workflows or activities registered, skipping worker initialization"
            )
            return

        # Create worker with registered workflows and activities
        self._worker = Worker(
            self._client,
            task_queue=self._config.task_queue,
            workflows=self._workflows,
            activities=self._activities,
            activity_executor=self._activity_executor
        )

        # Start worker in background task
        self._worker_task = asyncio.create_task(self._worker.run())
        logger.info(
            f"Temporal worker started on task queue: {self._config.task_queue} with "
            f"{len(self._workflows)} workflows and {len(self._activities)} activities"
        )

    async def close(self):
        """Close Temporal client and worker"""
        # Cancel connection retry loop

        if self._connection_task:
            self._connection_task.cancel()
            try:
                await self._connection_task
            except asyncio.CancelledError:
                pass

        if self._worker:
            await self._worker.shutdown()

        # Cancel worker task
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass

        # Shutdown activity executor
        self._activity_executor.shutdown(wait=True)

        logger.info("Temporal client closed")

    def is_connected(self) -> bool:
        """Check if connected to Temporal server"""
        return self._connected

    def _ensure_connected(self):
        """Ensure client is connected, raise error if not"""
        if not self._client:
            raise RuntimeError("Client not connected")

    def get_client(self) -> Optional[Client]:
        """Get the underlying Temporal client instance"""
        return self._client

    # Delegate common client operations to the underlying client

    async def start_workflow(self, *args, **kwargs):
        """Start a workflow and return its handle"""
        self._ensure_connected()
        return await self._client.start_workflow(*args, **kwargs)

    async def execute_workflow(self, *args, **kwargs):
        """Start a workflow and wait for completion"""
        self._ensure_connected()
        return await self._client.execute_workflow(*args, **kwargs)

    def get_workflow_handle(self, *args, **kwargs):
        """Get a workflow handle to an existing workflow by its ID"""
        self._ensure_connected()
        return self._client.get_workflow_handle(*args, **kwargs)

    def get_workflow_handle_for(self, *args, **kwargs):
        """Get a typed workflow handle to an existing workflow by its ID"""
        self._ensure_connected()
        return self._client.get_workflow_handle_for(*args, **kwargs)

    async def count_workflows(self, *args, **kwargs):
        """Count workflows"""
        self._ensure_connected()
        return await self._client.count_workflows(*args, **kwargs)

    def list_workflows(self, *args, **kwargs):
        """List workflows"""
        self._ensure_connected()
        return self._client.list_workflows(*args, **kwargs)

    async def create_schedule(self, *args, **kwargs):
        """Create a schedule and return its handle"""
        self._ensure_connected()
        return await self._client.create_schedule(*args, **kwargs)

    def get_schedule_handle(self, *args, **kwargs):
        """Get a schedule handle for the given ID"""
        self._ensure_connected()
        return self._client.get_schedule_handle(*args, **kwargs)

    async def list_schedules(self, *args, **kwargs):
        """List schedules"""
        self._ensure_connected()
        return await self._client.list_schedules(*args, **kwargs)

    def get_async_activity_handle(self, *args, **kwargs):
        """Get an async activity handle"""
        self._ensure_connected()
        return self._client.get_async_activity_handle(*args, **kwargs)

    async def execute_update_with_start_workflow(self, *args, **kwargs):
        """Send an update-with-start request and wait for the update to complete"""
        self._ensure_connected()
        return await self._client.execute_update_with_start_workflow(*args, **kwargs)

    async def start_update_with_start_workflow(self, *args, **kwargs):
        """Send an update-with-start request and wait for it to be accepted"""
        self._ensure_connected()
        return await self._client.start_update_with_start_workflow(*args, **kwargs)

    async def get_worker_build_id_compatibility(self, *args, **kwargs):
        """Get the Build ID compatibility sets for a specific task queue"""
        self._ensure_connected()
        return await self._client.get_worker_build_id_compatibility(*args, **kwargs)

    async def get_worker_task_reachability(self, *args, **kwargs):
        """Determine if some Build IDs for certain Task Queues could have tasks dispatched to them"""
        self._ensure_connected()
        return await self._client.get_worker_task_reachability(*args, **kwargs)

    async def update_worker_build_id_compatibility(self, *args, **kwargs):
        """Update the relative compatibility of Build IDs"""
        self._ensure_connected()
        return await self._client.update_worker_build_id_compatibility(*args, **kwargs)

    # Properties that delegate to the underlying client

    @property
    def namespace(self) -> str:
        """Namespace used in calls by this client"""
        if not self._client:
            return self._config.namespace
        return self._client.namespace

    @property
    def identity(self) -> str:
        """Identity used in calls by this client"""
        self._ensure_connected()
        return self._client.identity

    @property
    def data_converter(self):
        """Data converter used by this client"""
        self._ensure_connected()
        return self._client.data_converter

    @property
    def service_client(self):
        """Raw gRPC service client"""
        self._ensure_connected()
        return self._client.service_client

    @property
    def workflow_service(self):
        """Raw gRPC workflow service client"""
        self._ensure_connected()
        return self._client.workflow_service

    @property
    def operator_service(self):
        """Raw gRPC operator service client"""
        self._ensure_connected()
        return self._client.operator_service

    @property
    def test_service(self):
        """Raw gRPC test service client"""
        self._ensure_connected()
        return self._client.test_service

    def health_check(self) -> Dict[str, Any]:
        """Check if Temporal connection is healthy (non-blocking for health endpoints)"""
        if not self._connected:
            return {
                "connected": False,
                "status": "connecting",
                "last_error": self._last_connection_error
            }

        return {"connected": True, "status": "healthy"}
