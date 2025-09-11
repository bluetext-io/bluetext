"""
Example Temporal workflow using Pydantic models for type-safe data transfer.

This demonstrates the recommended patterns for Temporal workflows:
1. Using Pydantic models instead of raw parameters
2. Proper activity and workflow structure
3. Clear separation of concerns between orchestration and execution
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from typing import Optional

from pydantic import BaseModel
from temporalio import activity, workflow
from temporalio.client import Client
from temporalio.contrib.pydantic import pydantic_data_converter
from temporalio.worker import Worker


class ComposeGreetingInput(BaseModel):
    """
    Pydantic model for activity input parameters.

    IMPORTANT: Temporal strongly encourages using dataclasses or Pydantic models
    for activity parameters instead of multiple arguments. This allows for
    backwards-compatible field additions.

    NOTE: Binary data should be base64-encoded as strings. Complex objects may
    need custom converters. The pydantic_data_converter handles Pydantic model
    serialization automatically.
    """
    greeting: str
    name: str
    style: Optional[str] = "friendly"


class GreetingResponse(BaseModel):
    """Pydantic model for activity output"""
    message: str
    formatted_message: str


@activity.defn
def compose_greeting(input: ComposeGreetingInput) -> GreetingResponse:
    """
    Basic activity that performs the actual work.

    Activities are the "doers" in Temporal - they execute the actual business logic.
    Use @activity.defn for sync activities (runs in ThreadPoolExecutor).
    Use @activity.defn with async def for async activities.

    The activity.logger is automatically configured with workflow context.
    """
    activity.logger.info(f"Running activity with parameter {input}")

    basic_message = f"{input.greeting}, {input.name}!"

    return GreetingResponse(
        message=basic_message,
        formatted_message=f"[{input.style.upper()}] {basic_message}"
    )


@workflow.defn
class GreetingWorkflow:
    """
    Workflows orchestrate activities and define the business logic flow.

    Workflows must be deterministic - avoid random numbers, current time, or external API calls
    directly in workflow code. Use activities for non-deterministic operations.
    """

    @workflow.run
    async def run(self, name: str, greeting: str = "Hello") -> GreetingResponse:
        """
        The main workflow entry point.

        This method defines the workflow's execution logic. It can:
        - Execute activities with retries and timeouts
        - Make decisions based on activity results
        - Handle errors and compensate for failures
        - Wait for external signals or timers
        """
        workflow.logger.info(f"Running workflow with parameter {name}")

        # Create input for the activity using Pydantic model
        greeting_input = ComposeGreetingInput(
            greeting=greeting,
            name=name,
            style="professional"
        )

        # Execute activity with timeout
        # CRITICAL: For single argument, pass directly. For multiple, use args=[...]
        result = await workflow.execute_activity(
            compose_greeting,
            greeting_input,  # Single argument can be passed directly
            start_to_close_timeout=timedelta(seconds=10),
        )

        # Example with multiple arguments (would need args=[...]):
        # result = await workflow.execute_activity(
        #     some_activity,
        #     args=[arg1, arg2, arg3],  # Multiple args MUST be in a list!
        #     start_to_close_timeout=timedelta(seconds=10),
        # )

        return result


async def main():
    """
    Example of running both worker and client in the same process.

    In production, workers and clients typically run in separate processes:
    - Workers: Long-running services that execute workflows/activities
    - Clients: Applications that start workflows and query their state

    The pydantic_data_converter enables automatic Pydantic model serialization.
    """

    # Connect with Pydantic data converter for automatic model serialization
    client = await Client.connect(
        "localhost:7233",
        data_converter=pydantic_data_converter,
    )

    # Run worker with workflows and activities
    async with Worker(
        client,
        task_queue="hello-activity-task-queue",
        workflows=[GreetingWorkflow],
        activities=[compose_greeting],
        # ThreadPoolExecutor for sync activities
        activity_executor=ThreadPoolExecutor(5),
    ):
        # IMPORTANT: How to call workflows correctly:
        #
        # For workflows with multiple parameters, use args=[...]:
        result = await client.execute_workflow(
            GreetingWorkflow.run,
            args=["World", "Hello"],  # Pass multiple args as a list
            id="hello-activity-workflow-id",
            task_queue="hello-activity-task-queue",
        )
        print(f"Result: {result.message}")
        print(f"Formatted: {result.formatted_message}")

        # Alternative: For single parameter workflows, you can pass directly:
        # result = await client.execute_workflow(
        #     SingleParamWorkflow.run,
        #     "single_argument",  # Single arg can be passed directly
        #     id="workflow-id",
        #     task_queue="task-queue",
        # )


if __name__ == "__main__":
    asyncio.run(main())
