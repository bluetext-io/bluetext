# Workflow and Activity Registry
# 
# Coding agents should import their workflows and activities here
# to register them with the Temporal client.
#
# Example:
# from .my_workflows import MyWorkflow, my_activity
# 
# Then add them to the lists below:

from .examples import ExampleWorkflow, example_activity, example_async_activity

# Register your workflows here
# Coding agents: Add your workflow classes to this list
WORKFLOWS = [
    ExampleWorkflow,
]

# Register your activities here  
# Coding agents: Add your activity functions to this list
ACTIVITIES = [
    example_activity,
    example_async_activity,
]