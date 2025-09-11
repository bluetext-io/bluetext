"""
Example helper functions for starting workflows from FastAPI routes.

Usage in routes:
    from ..workflows.utils import start_greeting_workflow
    
    workflow_id = await start_greeting_workflow(
        request.app.state.temporal_client,
        "World"
    )
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..clients.temporal import TemporalClient

from .examples import GreetingWorkflow


async def start_greeting_workflow(
    temporal_client: "TemporalClient", 
    name: str
) -> str:
    """
    Start a greeting workflow and return its ID.
    
    Example of how to start a workflow from a route.
    """
    # Start workflow using the client's delegation method
    # Args: workflow.run method, *args_for_workflow, id, task_queue
    handle = await temporal_client.start_workflow(
        GreetingWorkflow.run,
        name,  # This gets passed to GreetingWorkflow.run
        id=f"greeting-{name}-{id(name)}",  # Unique workflow ID
        task_queue=temporal_client._config.task_queue,
    )
    return handle.id


async def get_workflow_result(
    temporal_client: "TemporalClient", 
    workflow_id: str
) -> str:
    """
    Get the result of a workflow by ID.
    
    Example of how to retrieve workflow results.
    """
    # Get handle to existing workflow
    handle = temporal_client.get_workflow_handle(workflow_id)
    # Wait for and return the result
    return await handle.result()