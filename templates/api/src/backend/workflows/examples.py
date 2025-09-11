import asyncio
import logging
from datetime import timedelta

from temporalio import activity, workflow

logger = logging.getLogger(__name__)


# Example Activities
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


# Example Workflows
# These serve as templates - modify or replace with your own business logic

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