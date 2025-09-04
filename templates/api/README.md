# {{ project-name }}

A FastAPI app with support for both PostgreSQL and Couchbase with generic helper functions for rapid development.

## 🛠️ Development instructions

### Hook up to a database

**For PostgreSQL:**
1. Set USE_POSTGRES=true in `src/backend/conf.py`.
2. Build out the postgres-related routes you want in `src/backend/routes.py` (there are example routes at the bottom).

**For Couchbase:**
1. Set USE_COUCHBASE=true in `src/backend/conf.py`.
2. Build out the couchbase-related routes you want in `src/backend/routes.py` (there are example routes at the bottom).

## 🔧 Configuration

All configuration done via env vars using Polytope. Don't worry about it. If you add more environment variables that need to be set, add them to `polytope.yml` as well.

## 🔍 Health Checks

The template includes a health check endpoint that verifies database connectivity at `GET /health`.
