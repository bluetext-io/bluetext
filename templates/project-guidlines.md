# ABOUT THIS PROJECT

This is a Bluetext project - a containerized full-stack application orchestrated using Polytope.

## PROJECT STRUCTURE

- **Frontend**: React + shadcn/ui + React Router v7 (modules/frontend or modules/<service-name>)
- **API**: FastAPI + SQLModel + uv for Python (modules/api or modules/<service-name>)
- **Databases**: PostgreSQL, Couchbase (modules/postgres, modules/couchbase)
- **Shared Libraries**: lib/py/* for Python shared code
- **All services run in containers with hot reload enabled**

## ⚠️ CRITICAL: MANDATORY BEFORE ANY CODE CHANGES ⚠️

**YOU MUST CALL THESE TOOLS BEFORE MAKING ANY CODE CHANGES:**

1. **FIRST**: Call `list-ai-dev-context-scopes` to see available context scopes
2. **SECOND**: Call `get-ai-dev-context(scope: <scope-name>)` to retrieve critical guidelines:
   - **"general"** - Project overview, MCP tools, environment variables
   - **"api"** - API routes, authentication, Temporal workflows, Couchbase models, import paths
   - **"frontend"** - Import paths, theming, shadcn components, routing patterns
3. **THIRD**: Follow the retrieved guidelines to prevent breaking changes

**These guidelines contain critical information about:**
- Import paths and module structure
- Authentication patterns and middleware
- Database schemas and models
- Component patterns and styling conventions
- Environment variable usage

**Skipping this step WILL cause errors and breaking changes.**
