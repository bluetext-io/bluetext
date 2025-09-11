import asyncio
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Optional, List, Any

from temporalio.client import Client
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
    Generic Temporal client for workflow management.

    Handles connection to Temporal server and provides methods to start,
    query, and manage workflows.

    Accepts workflows and activities as constructor parameters.
    """

    def __init__(
        self,
        config: TemporalConf,
        workflows: Optional[List[Any]] = None,
        activities: Optional[List[Any]] = None
    ):
        self._config = config
        self._workflows = workflows or []
        self._activities = activities or []
        self._client: Optional[Client] = None
        self._worker: Optional[Worker] = None
        self._connected = False
        self._worker_task = None
        self._connection_task = None
        self._last_connection_error = None
        self._last_error_log_time = 0
        self._activity_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="temporal-activity")

    async def initialize(self):
        """Initialize Temporal client and start connection retry loop in background"""
        logger.info("Temporal client initialized")
        self._connection_task = asyncio.create_task(self._connection_retry_loop())

    async def _connection_retry_loop(self):
        """Retry connection loop that runs in background"""
        while not self._connected:
            try:
                logger.info(
                    f"Connecting to Temporal server at {self._config.get_target_host()}"
                )
                self._client = await Client.connect(
                    self._config.get_target_host(),
                    namespace=self._config.namespace
                )

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
        if not self._client:
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
        logger.info(f"Temporal worker started on task queue: {self._config.task_queue} "
                    f"with {len(self._workflows)} workflows and {len(self._activities)}"
                    " activities")

    async def close(self):
        """Close Temporal client and worker"""
        # Cancel connection retry loop
        if self._connection_task:
            self._connection_task.cancel()
            try:
                await self._connection_task
            except asyncio.CancelledError:
                pass

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

    def get_client(self) -> Optional[Client]:
        """Get the Temporal client instance"""
        return self._client

    def is_connected(self) -> bool:
        """Check if connected to Temporal server"""
        return self._connected

    # Delegation methods for common workflow operations

    async def start_workflow(self, *args, **kwargs):
        """Start a workflow, delegating to underlying client"""
        if not self._connected or not self._client:
            raise RuntimeError("Temporal client not connected")
        return await self._client.start_workflow(*args, **kwargs)

    def get_workflow_handle(self, *args, **kwargs):
        """Get workflow handle, delegating to underlying client"""
        if not self._connected or not self._client:
            raise RuntimeError("Temporal client not connected")
        return self._client.get_workflow_handle(*args, **kwargs)

    async def execute_workflow(self, *args, **kwargs):
        """Execute a workflow and wait for result, delegating to underlying client"""
        if not self._connected or not self._client:
            raise RuntimeError("Temporal client not connected")
        return await self._client.execute_workflow(*args, **kwargs)