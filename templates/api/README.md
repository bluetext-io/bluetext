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
1. Enable in `src/backend/conf.py`:
```python
USE_POSTGRES = True
```

2. Check logs to verify connection:
```mcp
__polytope__get_container_logs(container: {{ project-name }}, limit: 50)
```

3. Test database health via health endpoint:
```bash
curl http://localhost:3030/health
```

4. Add database routes in `src/backend/routes/base.py`:
```python
from ..utils import DBSession

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
- ✅ **Use `workflow.sleep()`** for delays: `await workflow.sleep(3)`
- ✅ **Handle `wait_condition` correctly**: Don't check `if not result` after wait_condition
- ❌ **Never use `asyncio.sleep()`** in workflows - breaks determinism
- ✅ **Activities need own DB connection** - cannot access app state
- ✅ **Use Pydantic models** for activity inputs/outputs

### API Response Handling
- ✅ **Convert UUIDs to strings**: Use `UserResponse.from_model(user)` pattern
- ✅ **Separate request/response models**: Don't use SQLModel directly in API responses
- ✅ **Handle type conversions explicitly**: String IDs in URLs, UUID objects in database

### Architecture Decisions
- **Primary Keys**: UUID7 for uniqueness, ordering, and no auto-increment issues
- **Database Sessions**: Auto-commit pattern prevents manual transaction management errors
- **Temporal Integration**: Activities are stateless with dedicated connections
- **Type Safety**: Explicit conversion between UUID and string types

## 🛠️ Development instructions

**For PostgreSQL:**
1. Set USE_POSTGRES=true in `src/backend/conf.py`.
2. Build out the postgres-related routes you want in `src/backend/routes.py` (there are example routes at the bottom).
3. **IMPORTANT**: Always use `DBSession` from `routes/utils.py` for database access in routes:
   ```python
   from .utils import DBSession
   from ..db.utils import pk_field

   class User(SQLModel, table=True):
       id: str = pk_field()  # UUID7 primary key
       email: str = Field(unique=True, index=True)

   @router.post("/users")
   async def create_user(user: User, session: DBSession):
       # DBSession auto-commits - NEVER call session.commit() or session.flush()
       return await create_user_db(session, user)
   ```
   **CRITICAL: Never call `session.flush()` in database functions - causes database errors!**

### SMS/Twilio
1. Set Twilio environment variables
2. Enable: `USE_TWILIO = True` in `conf.py`
3. Uncomment SMS routes in `routes/base.py`

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
