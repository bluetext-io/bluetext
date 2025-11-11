# Couchbase

This module sets up a Couchbase server for development.

## Adding Couchbase Client to API

If this project has a bluetext API, you can connect to the Couchbase server programmatically through the Couchbase client.

**There are ONLY two valid ways to call this tool:**

**Option 1** - Direct tool call (if available):
```mcp
__polytope__{{ project-name }}-add-couchbase-client()
```

**Option 2** - Using the run tool (if direct tool not available):
```mcp
__polytope__run(tool: "{{ project-name }}-add-couchbase-client", args: {})
```

where `project-name` is the name of your API service (e.g., if your API is named "api", the tool name is "api-add-couchbase-client")

**DO NOT use any other format such as:**
- ❌ `api/add-couchbase-client`
- ❌ `tool: "api/add-couchbase-client"`
- ❌ Any path-based format

## Managing Couchbase Resources

Couchbase buckets, scopes, and collections are managed through the config-manager module. See the config-manager README for details on:
- Defining keyspaces in `couchbase.yaml`
- Seeding data with JSON files
