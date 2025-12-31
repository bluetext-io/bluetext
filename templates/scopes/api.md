# API Development Guidelines

FastAPI template with hot reload development.

## Hot Reload

The server runs with hot reload enabled. **No manual restarts needed** - changes are automatically applied when you save files.

**ALWAYS check logs after making changes:**
```mcp
get-container-logs(container: <api-name>, limit: 50)
```

Look for import errors, syntax errors, or runtime exceptions.

**Note**: The only time a manual restart is required is when adding new environment variables to polytope.yml.

## Quick Start

```mcp
# Check service status
list-services()

# View recent logs
get-container-logs(container: <api-name>, limit: 50)

# Test the API
curl http://localhost:3030/health
```

## Key Files

- `src/backend/conf.py` - Feature toggles and configuration
- `src/backend/routes/base.py` - Add your API endpoints here
- `src/backend/routes/utils.py` - Database helpers (DBSession, RequestPrincipal)
- `src/backend/workflows/` - Temporal workflow definitions
- `polytope.yml` - Container and environment configuration

## Authentication

1. Enable: `USE_AUTH = True` in `conf.py`
2. Configure JWT authentication (JWK URL, audience, etc.)
3. Protect routes with `RequestPrincipal` dependency:

```python
from ..utils import RequestPrincipal

@router.get("/protected")
async def protected_route(principal: RequestPrincipal):
    # principal.claims contains the decoded JWT claims
    return {"claims": principal.claims}
```

Clients must send `Authorization: Bearer <jwt-token>` header.

## Temporal Workflows

### Setup

1. Add Temporal Server: `add-temporal()`
2. Add Temporal client: `run(tool: <api-name>-add-temporal-client, args: {})`
3. Scaffold a workflow: `run(tool: <api-name>-add-temporal-workflow, args: {name: "workflow-name"})`

### Best Practices

**Import dependencies INSIDE activity functions, not at module level:**

```python
@activity.defn
def my_activity(input: MyInput) -> MyOutput:
    # CORRECT: Import inside activity
    from couchbase_client import get_client
    from google import genai

    client = get_client()
    return MyOutput(...)
```

## Couchbase

### Setup

```mcp
run(tool: <api-name>-add-couchbase-client, args: {})
```

This adds the client library, configures environment variables, sets up model initialization, and registers hooks in FastAPI lifespan.

### Creating Models

```mcp
run(tool: <api-name>-add-couchbase-model, args: {name: "model-name"})
```

Generates a model with Pydantic validation and automatic collection initialization. **DO NOT create model files manually** - always use the tool.

## Adding Dependencies

```mcp
run(tool: <api-name>-add, args: {packages: "package-name"})
```

## Development Workflow

1. **Make changes** - Edit any `.py` file
2. **Check logs immediately** - `get-container-logs(container: <api-name>, limit: 50)`
3. **Test changes** - `curl http://localhost:3030/your-route`
4. **Fix errors before continuing** - Don't move on until it works

Hot reload means instant feedback - use it! Always check logs after saving files.
