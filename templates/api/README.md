# {{ project-name }}

A FastAPI app with support for both PostgreSQL and Couchbase with generic helper functions for rapid development.

## 🚀 Running the API

**The API is automatically started when you created it using `add-{{ project-name }}`.**

To inspect which steps run, use: `list-services-in-job`
To view logs, use: `get-logs-in-job{"step":"backend"}`

**Do not manually run the `{{ project-name }}` module - it's already running by calling `add-{{ project-name }}`.**

## 🛠️ Development instructions

**For PostgreSQL:**
1. Set USE_POSTGRES=true in `src/backend/conf.py`.
2. Build out the postgres-related routes you want in `src/backend/routes.py` (there are example routes at the bottom).

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

## 🔧 Configuration

All configuration done via env vars using Polytope. Don't worry about it. If you add more environment variables that need to be set, add them to `polytope.yml` as well.

## 🔍 Health Checks

The template includes a health check endpoint that verifies database connectivity at `GET /health`.
