import asyncio
import logging
from dataclasses import dataclass
from datetime import timedelta
from typing import Optional

from temporalio import activity, workflow
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
    Temporal client for workflow management.
    
    Handles connection to Temporal server and provides methods to start,
    query, and manage workflows.
    
    Only initializes if USE_TEMPORAL is True in configuration.
    """
    
    def __init__(self, config: Optional[TemporalConf] = None):
        self._config = config
        self._client: Optional[Client] = None
        self._worker: Optional[Worker] = None
        self._initialized = False
        self._connected = False
        self._worker_task = None
    
    async def initialize(self):
        """Initialize the Temporal client"""
        if not self._config:
            raise ValueError("TemporalConf required")
        
        self._initialized = True
        logger.info("Temporal client initialized")
    
    async def init_connection(self):
        """Initialize connection to Temporal server"""
        if not self._initialized:
            return
        
        try:
            logger.info(f"Connecting to Temporal server at {self._config.get_target_host()}")
            self._client = await Client.connect(
                self._config.get_target_host(),
                namespace=self._config.namespace
            )
            self._connected = True
            logger.info("Connected to Temporal server")
            
            # Initialize and start worker
            await self._init_worker()
            
        except Exception as e:
            logger.error(f"Failed to connect to Temporal: {e}")
            self._connected = False
            raise
    
    async def _init_worker(self):
        """Initialize and start Temporal worker"""
        if not self._client:
            return
        
        # Create worker with example workflows and activities
        self._worker = Worker(
            self._client,
            task_queue=self._config.task_queue,
            workflows=[ExampleWorkflow],
            activities=[example_activity, example_async_activity]
        )
        
        # Start worker in background task
        self._worker_task = asyncio.create_task(self._worker.run())
        logger.info(f"Temporal worker started on task queue: {self._config.task_queue}")
    
    async def close(self):
        """Close Temporal client and worker"""
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        
        if self._client:
            await self._client.close()
            self._connected = False
        
        logger.info("Temporal client closed")
    
    def get_client(self) -> Optional[Client]:
        """Get the Temporal client instance"""
        return self._client
    
    def is_connected(self) -> bool:
        """Check if connected to Temporal server"""
        return self._connected


# Example Workflows and Activities
# These serve as templates - modify or replace with your own business logic

@activity
def example_activity(name: str) -> str:
    """Example synchronous activity"""
    logger.info(f"Running example activity with name: {name}")
    return f"Hello, {name} from activity!"


@activity
async def example_async_activity(delay_seconds: int) -> str:
    """Example asynchronous activity with delay"""
    logger.info(f"Running async activity with {delay_seconds}s delay")
    await asyncio.sleep(delay_seconds)
    return f"Completed async activity after {delay_seconds} seconds"


@workflow.defn
class ExampleWorkflow:
    """
    Example workflow that demonstrates basic Temporal patterns.
    
    This workflow:
    1. Runs a simple activity
    2. Runs an async activity with delay
    3. Returns combined results
    """
    
    @workflow.run
    async def run(self, name: str, delay_seconds: int = 2) -> str:
        """Main workflow method"""
        
        # Run synchronous activity
        result1 = await workflow.execute_activity(
            example_activity,
            name,
            start_to_close_timeout=timedelta(seconds=30)
        )
        
        # Run asynchronous activity
        result2 = await workflow.execute_activity(
            example_async_activity,
            delay_seconds,
            start_to_close_timeout=timedelta(seconds=60)
        )
        
        return f"Workflow completed: {result1} | {result2}"


# Example usage functions for FastAPI routes

async def start_example_workflow(temporal_client: TemporalClient, name: str, delay_seconds: int = 2) -> str:
    """
    Example function to start the example workflow.
    Use this pattern in your FastAPI routes.
    """
    if not temporal_client.is_connected():
        raise RuntimeError("Temporal client not connected")
    
    client = temporal_client.get_client()
    if not client:
        raise RuntimeError("Temporal client not available")
    
    # Start workflow
    handle = await client.start_workflow(
        ExampleWorkflow.run,
        name,
        delay_seconds,
        id=f"example-workflow-{name}-{asyncio.get_event_loop().time()}",
        task_queue=temporal_client._config.task_queue
    )
    
    logger.info(f"Started workflow with ID: {handle.id}")
    return handle.id


async def get_workflow_result(temporal_client: TemporalClient, workflow_id: str) -> str:
    """
    Example function to get workflow result.
    Use this pattern in your FastAPI routes.
    """
    if not temporal_client.is_connected():
        raise RuntimeError("Temporal client not connected")
    
    client = temporal_client.get_client()
    if not client:
        raise RuntimeError("Temporal client not available")
    
    # Get workflow handle and result
    handle = client.get_workflow_handle(workflow_id)
    result = await handle.result()
    
    return result