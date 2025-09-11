import asyncio
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..clients.temporal import TemporalClient

from .examples import ExampleWorkflow

logger = logging.getLogger(__name__)


# Example usage functions for FastAPI routes
# Coding agents: Create similar functions for your workflows

async def start_example_workflow(temporal_client: "TemporalClient", name: str, delay_seconds: int = 2) -> str:
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


async def get_workflow_result(temporal_client: "TemporalClient", workflow_id: str) -> str:
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