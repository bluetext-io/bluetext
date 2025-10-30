# Temporal Client

A standalone Temporal client library with async support for building workflow-based applications.

## Features

- Async connection retry with health checks
- Worker management with activity executor
- Pydantic data converter support
- Connection state management
- Graceful shutdown

## Installation

```bash
uv add --editable ../lib/py/temporal-client
```

## Usage

```python
from temporal_client import TemporalClient, TemporalConf

# Configure client
config = TemporalConf(
    host="temporal",
    port=7233,
    namespace="default",
    task_queue="main-task-queue"
)

# Initialize client with workflows and activities
client = TemporalClient(
    config=config,
    workflows=[MyWorkflow],
    activities=[my_activity]
)

await client.initialize()

# Use client
handle = await client.start_workflow(
    MyWorkflow.run,
    args=[input_data],
    id="workflow-id",
    task_queue=config.task_queue
)

result = await handle.result()
```
