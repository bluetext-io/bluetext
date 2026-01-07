# ABOUT THIS PROJECT
This project runs containerized and is orchestrated using Polytope. To interact with the running services and manage the project, specific built-in Polytope mcp tools are available.
A list of running apps can be accessed by calling the `__polytope_mcp__list-containers` tool. To list all containers that expose services and the ports they are accessible on, use the `__polytope_mcp__list-services` tool.
Aside from Polytopes built-in tools, further tools served through the mcp can be defined in `polytope.yaml`. Each module that can be added through the `__polytope_mcp__add-*` tools will be scaffolded with its own Polytope file. This file is automatically added as an included to the Polytope file in the root of this project and includes all necessary configuration to run the module, plus tools relevant for development with this specific module.

# BEFORE MAKING CHANGES

1. call the `__polytope_mcp__list-context-scopes()` tool to list all available AI guidelines.
2. call the `__polytope_mcp__get-context{scope: scope-name)` tool to retrieve the current project guidelines.
3. Review the retrieved guidelines to ensure compliance during development.

# GENERAL DEVELOPMENT GUIDELINES
## FEATURE IMPLEMENTATION

1. After each implementation step, run the `__polytope_mcp__get-logs` tool to check for any warnings or errors.

## INJECTING ENVIRONMENT VARIABLES INTO CONTAINERS

1. Navigate to the polytope file that defines the container you want to inject into. For an API called `ai-chat-api`, this would be `modules/ai-chat-api/polytope.yml`.
2. Locate the `env` block under `run: - tool: <polytope-tool> args: env:` (e.g. `polytope/python`) and add the variable:
   ```yaml
   env:
     - { name: MY_ENV_VAR, value: my-value }
   ```
3. For security-critical env vars (API keys, secrets): use `pt.secret <secret-name>` as the value:
   ```yaml
   env:
     - { name: MY_API_KEY, value: pt.secret my-api-key }
   ```
   Then prompt the user to set the secret by running: `pt secrets set my-api-key <their-api-key>`
4. Prompt the user to restart the server manually to correctly load the new env var. While the Polytope sandbox is down, no MCP tools are available.
