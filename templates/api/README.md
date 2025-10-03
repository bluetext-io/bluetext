# {{ project-name }}

A FastAPI app with support for both PostgreSQL and Couchbase with generic helper functions for rapid development.

## 🚀 Running the API

**The API is automatically started when you created it using `add-{{ project-name }}`.**

To inspect which steps run, use: `list-services-in-job`
To view logs, use: `get-logs-in-job{"step":"backend"}`

**Do not manually run the `{{ project-name }}` module - it's already running by calling `add-{{ project-name }}`.**

## 🧰 Available Development Tools

{{ project-name }}-lint      # Run linting checks
{{ project-name }}-format    # Format code
{{ project-name }}-validate  # Development validation

execute like:
`run("module": "{{ project-name }}-validate", "args": [])`

validate will check for common issues like:
- Python version compatibility
- UUID usage patterns
- Enum value conventions
- Temporal workflow patterns
- Database type consistency


## ⚠️ CRITICAL PATTERNS - Avoid Common Mistakes

### Database Models
- ✅ **Use UUID7 primary keys**: `id: str = pk_field()`
- ✅ **Enum values lowercase**: `STATUS = "active"` (not `"ACTIVE"`)
- ✅ **API responses use strings**: `"id": str(model.id)`
- ❌ **Never call `session.flush()`** in database functions - causes "NULL identity key" errors
- ✅ **Let DBSession auto-commit** - no manual commits needed

### Temporal Workflows
1. Enable: `USE_TEMPORAL = True` in `conf.py`
2. Add workflows to `src/backend/workflows/examples.py`
3. Register workflows and activities in `src/backend/workflows/__init__.py`
4. Uncomment workflow routes in `src/backend/routes/base.py`

### Couchbase

Quick Setup - ALWAYS follow this pattern for new Couchbase collections:

1. Enable: `USE_COUCHBASE = True` in `conf.py`
2. Add desired collections - Run this tool:
   ```mcp
   __polytope__run(module: "{{ project-name }}-add-couchbase-collection", args: {"name": "collection-name"})
   ```
   During initial setup, finish and verify this step before adding further services to the project.
3. Check container logs to verify success:
   ```mcp
   __polytope__get_container_logs(container: {{ project-name }}, limit: 50)
   ```
4. Read the generated file at: `src/backend/couchbase/collections/<collection_name>.py`
5. Customize the model in the generated file (DO NOT create manually)
6. Uncomment example routes in `routes/base.py`

**For Couchbase:**
1. Set USE_COUCHBASE=true in `src/backend/conf.py`.
2. Build out the couchbase-related routes you want in `src/backend/routes.py` (there are example routes at the bottom).

**For Auth:**
1. Set USE_AUTH=true in `src/backend/conf.py`.
2. Use the `RequestPrincipal` dependency in your routes to protect them.
3. Optionally, add custom variants of `RequestPrincipal` to filter on roles or similar.

**For Temporal:**
1. Set USE_TEMPORAL=true in `src/backend/conf.py`.
2. Uncomment the example routes in `src/backend/routes/base.py` to test workflows.
3. Add your workflows and activities to `src/backend/workflows/` (see examples in `workflows/examples.py`).
4. Register them in `src/backend/workflows/__init__.py` by adding to the WORKFLOWS and ACTIVITIES lists.

**For Twilio SMS:**
1. Set USE_TWILIO=true in `src/backend/conf.py`.
2. Set the required environment variables: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_FROM_PHONE_NUMBER.
3. Uncomment the SMS routes in `src/backend/routes/base.py` to enable SMS functionality.
4. Optionally combine with Temporal workflows for delayed/scheduled SMS messages.

**For Twilio SMS:**
1. Set USE_TWILIO=true in `src/backend/conf.py`.
2. Set the required environment variables: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_FROM_PHONE_NUMBER.
3. Uncomment the SMS routes in `src/backend/routes/base.py` to enable SMS functionality.
4. Optionally combine with Temporal workflows for delayed/scheduled SMS messages.

## 🔧 Configuration

All configuration done via env vars using Polytope. Don't worry about it. If you add more environment variables that need to be set, add them to `polytope.yml` as well.

## 🔍 Health Checks

The template includes a health check endpoint that verifies database connectivity at `GET /health`.
