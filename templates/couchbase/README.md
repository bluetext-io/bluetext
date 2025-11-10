## COUCHBASE

If this project already has a bluetext API, you can connect to the couchbase server programatically through the couchbase client.

### Adding Couchbase Client to API

**IMPORTANT: There are ONLY two valid ways to call this tool. Use EXACTLY one of these formats:**

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
# When generating seed data, create the .JSON file of the data in the seeds directory of the config manager, and run the following tool:

 ```mcp
 __polytope__run(tool: seed-couchbase)
 ```

