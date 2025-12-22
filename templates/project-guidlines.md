# ABOUT THIS PROJECT

This project runs containerized and is orchestrated using Polytope.

## Before Making Changes

1. Call `list-ai-dev-context-scopes` to see available context scopes
2. Call `get-ai-dev-context(scope: <scope-name>)` to retrieve guidelines for your specific task (defaults to "general")
3. Review the retrieved guidelines to ensure compliance during development

## Available Scopes

- **general** - Project overview, MCP tools, environment variables
- **api** - API development: hot reload, routes, authentication, Temporal, Couchbase
- **frontend** - Frontend development: import paths, theming, shadcn components
