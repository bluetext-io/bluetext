from dataclasses import dataclass
from datetime import timedelta

from temporalio import activity, workflow


# Activities are functions that do the actual work
# Use @activity.defn for async activities, @activity for sync activities
@activity.defn
async def greet_user(name: str) -> str:
    """Example activity that greets a user"""
    return f"Hello, {name}!"


# Workflows orchestrate activities
@workflow.defn
class GreetingWorkflow:
    @workflow.run
    async def run(self, name: str) -> str:
        # Execute an activity with timeout
        # Args: activity_function, *args_for_activity, timeout_config
        return await workflow.execute_activity(
            greet_user,
            name,  # This gets passed to greet_user
            start_to_close_timeout=timedelta(seconds=10),
        )