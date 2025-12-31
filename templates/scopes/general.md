# General Development Guidelines

This project runs containerized and is orchestrated using Polytope. Interact with running services and manage the project through built-in Polytope MCP tools.

## Before Making Changes

1. Call `list-ai-dev-context-scopes` to see all available context scopes
2. Call `get-ai-dev-context(scope: <scope-name>)` to retrieve guidelines for your specific task
3. Review the retrieved guidelines to ensure compliance during development

## Key MCP Tools

- `list-containers` - List running containers
- `list-services` - List services with their exposed ports
- `list-steps` - List steps that have been run (understand project state)
- `get-container-logs(container: <name>, limit: N)` - View container logs

## After Making Code Changes

**MANDATORY**: Check container logs after any code modification:
```mcp
get-container-logs(container: <service-name>, limit: 25)
```

All running services have hot reload enabled. No manual restarts necessary. Errors will surface when invalid code changes are made. Always check for import errors, syntax errors, or runtime exceptions.

## After Adding Services or Functionality

Always run `list-tools` after calling any tool that adds new services or functionality:
- After `add-frontend`, `add-api`, `add-postgres`, `add-couchbase`, `add-temporal`
- After adding client libraries (e.g., `api-add-couchbase-client`, `api-add-temporal-client`)
- After any tool that modifies service capabilities

## Environment Variables

To inject environment variables into containers:

1. Navigate to the polytope file that defines the container (e.g., `modules/<service-name>/polytope.yml`)
2. Locate the `env` block within the tool's `run` section:

```yaml
tools:
  api:
    run:
      - tool: polytope/python
        args:
          env:
            - { name: HTTP_PORT, value: 3030 }
            - { name: LOG_LEVEL, value: INFO }
            - { name: POSTGRES_HOST, value: postgres }
            - { name: API_KEY, value: pt.secret api-key }
```

3. For security-critical variables (API keys, tokens, credentials), use `pt.secret <secret-name>`:
```bash
pt secrets set <secret-name> <secret-value>
```

4. Prompt the user to restart the server manually to load new env vars. While the Polytope sandbox is down, no MCP tools are available.

## Project Structure

Each module added through `add-*` tools is scaffolded with its own `polytope.yml` file, automatically included in the root configuration. This file contains all necessary configuration plus tools relevant for development with that specific module.
