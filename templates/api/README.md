# {{ project-name }}

FastAPI template with PostgreSQL, Couchbase, Temporal, and Twilio support - designed for instant hot reload development.

## Development Notes

**The server runs with hot reload enabled** - Your changes are automatically applied when you save files. No manual restarts needed.

**ALWAYS check logs after making changes**: After any code change, verify it worked by checking the server logs:
```mcp
__polytope__get_container_logs(container: {{ project-name }}, limit: 50)
```
Look for import errors, syntax errors, or runtime exceptions. The hot reload will show if your code loaded successfully or if there are any errors.

**Note**: If this project was created using the `add-api` tool, your API service runs in a container that you can access and observe through MCP commands.

## Quick Start

```mcp
# Check service status
__polytope__list_services()

# View recent logs
__polytope__get_container_logs(container: {{ project-name }}, limit: 50)

# Test the API
curl http://localhost:3030/health
```

## API Endpoints

### Active Endpoints
- Health check: `GET /health` - Comprehensive health check with service status

### Example Endpoints (commented out)
The template includes commented-out example routes for:
- PostgreSQL user management
- Couchbase user operations
- Temporal workflow execution
- Twilio SMS sending

Uncomment and adapt these examples in `src/backend/routes/base.py` as needed.

## Setting Up Features

### PostgreSQL Database

1. Add the PostgreSQL client:
```mcp
__polytope__run(tool: {{ project-name }}-add-postgres-client, args: {})
```

2. Check logs to verify connection:
```mcp
__polytope__get_container_logs(container: {{ project-name }}, limit: 50)
```

3. Test database health via health endpoint:
```bash
curl http://localhost:3030/health
```

4. Use the DBSession dependency in your routes:
```python
from ..routes.utils import DBSession

@router.post("/test-db")
async def test_database(session: DBSession):
    # DBSession auto-commits - NEVER call session.commit()
    return {"status": "connected"}
```

### Authentication
1. Enable: `USE_AUTH = True` in `conf.py`
2. Configure JWT authentication in environment/config (JWK URL, audience, etc.)
3. Protect any route by adding `RequestPrincipal` as a dependency - this validates JWT tokens from Authorization headers:
```python
from ..utils import RequestPrincipal

@router.get("/protected")
async def protected_route(principal: RequestPrincipal):
    # principal.claims contains the decoded JWT claims
    return {"claims": principal.claims}
```
4. Clients must send requests with `Authorization: Bearer <jwt-token>` header

### Temporal Workflows

#### Setup

1. Add the Temporal Server to the project:
```mcp
__polytope__add-temporal()
```

2. Add the Temporal client to the API:
```mcp
__polytope__run(tool: {{ project-name }}-add-temporal-client, args: {})
```

3. Scaffold a new workflow in the API:
```mcp
__polytope__run(tool: {{ project-name }}-add-temporal-workflow, args: {name: "workflow-name"})
```

#### Best Practices

**Activity Imports**: Always import dependencies INSIDE activity functions, not at module level:

```python
@activity.defn
def my_activity(input: MyInput) -> MyOutput:
    # ✅ CORRECT: Import inside activity
    from couchbase_client import get_client
    from google import genai

    # Activity logic here
    client = get_client()
    return MyOutput(...)
```

### Couchbase

#### Setup

Add the Couchbase client library to your project:

```mcp
__polytope__run(tool: {{ project-name }}-add-couchbase-client, args: {})
```

This will:
- Add the couchbase-client library as an editable dependency
- Configure Couchbase environment variables in `polytope.yml`
- Set up model initialization and directory structure
- Register initialization hooks in your FastAPI lifespan

#### Creating Models

Once the client is set up, create models using:

```mcp
__polytope__run(tool: {{ project-name }}-add-couchbase-model, args: {name: "model-name"})
```

This generates a model with Pydantic validation and automatic collection initialization. Check logs after creation, then add your fields to the generated file in `src/backend/couchbase/models/`.

**Important**: DO NOT create model files manually - always use the tool.

### SMS/Twilio

1. Add the Twilio client:
```mcp
__polytope__run(tool: {{ project-name }}-add-twilio-client, args: {})
```

2. Configure Twilio credentials in polytope.yml environment variables:
   - TWILIO_ACCOUNT_SID
   - TWILIO_AUTH_TOKEN
   - TWILIO_FROM_PHONE_NUMBER

3. Use the TwilioSMS dependency in routes or register the generated sms router

---

**Note on MCP Tools**: All tools shown using `__polytope__run(tool: ...)` can be called directly if available. For example, instead of `__polytope__run(tool: {{ project-name }}-add-postgres-client, args: {})`, you can use `__polytope__{{ project-name }}-add-postgres-client()`.

## Development Workflow

1. **Make changes** - Edit any `.py` file
2. **Check logs immediately**:
   ```mcp
   __polytope__get_container_logs(container: {{ project-name }}, limit: 50)
   ```
3. **Test changes** - `curl http://localhost:3030/your-route`
4. **Fix errors before continuing** - Don't move on until it works

## Key Files

- `src/backend/conf.py` - Feature toggles and configuration
- `src/backend/routes/base.py` - Add your API endpoints here
- `src/backend/routes/utils.py` - Database helpers (DBSession, RequestPrincipal)
- `src/backend/workflows/` - Temporal workflow definitions
- `polytope.yml` - Container and environment configuration

## Adding Dependencies to the API

If you want to add dependencies to the API, run: 
```mcp
mcp__polytope-mcp__run(tool: "{{{ project-name }}api-add", args: {"packages": "package-name"})
```
## Debugging

**Always start with logs when something doesn't work:**
```mcp
__polytope__get_container_logs(container: {{ project-name }}, limit: 100)
```

Common checks:
1. **Service running**: `__polytope__list_services()`
2. **Health endpoint**: `curl http://localhost:3030/health`
3. **Configuration**: Check feature flags in `conf.py`
4. **Hot reload status**: Look for reload messages in logs

**Critical**: Hot reload means instant feedback - use it! Always check logs after saving files.
