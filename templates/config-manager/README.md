# Config Manager

Manages Couchbase buckets/scopes/collections and Redpanda topics with continuous monitoring and data seeding capabilities.

## How It Works

The config-manager runs continuously, monitoring the `conf/seeds` directory for changes. When files are added or modified, it automatically processes them:

1. **YAML files** (`.yaml`, `.yml`) - Define bucket/scope/collection structure or topics
2. **JSON files** (`.json`) - Seed data into Couchbase collections

## Couchbase Configuration

### 1. Define Keyspaces in `couchbase.yaml`

Before seeding data, you must define the bucket, scope, and collection in `conf/couchbase.yaml`:

```yaml
buckets:
  main:
    defaults:
      ram_quota_mb: 256
      num_replicas: 0
    scopes:
      api:
        collections:
          users:
            defaults:
              max_ttl: 0
```

### 2. Seed Data with JSON Files

Once the keyspace is defined, add JSON seed files to `conf/seeds/` using the naming format:

**Format**: `bucket.scope.collection.json`

**Example**: `main.api.users.json`

```json
[
  {
    "id": "user:1",
    "name": "John Doe",
    "email": "john@example.com"
  },
  {
    "id": "user:2",
    "name": "Jane Smith",
    "email": "jane@example.com"
  }
]
```

**Important Notes:**
- Each document MUST have an `id` field (this becomes the document key)
- The `id` field is removed from the document data when inserted
- Seeding uses upsert mode by default (updates existing documents)
- The keyspace (bucket.scope.collection) MUST already be defined in `couchbase.yaml`

### 3. Automatic Processing

The config-manager watches `conf/seeds/` and will automatically:
1. Process `couchbase.yaml` to create buckets/scopes/collections
2. Process any YAML seed files in `conf/seeds/` for additional resources
3. Process any JSON seed files in `conf/seeds/` to insert data

## Directory Structure

```
conf/
├── config.yaml          # Environment configuration
├── couchbase.yaml       # Couchbase resource definitions
└── seeds/              # Seed files (watched by config-manager)
    ├── .gitkeep
    ├── EXAMPLE.main.api.users.json
    └── [your-seed-files.json]
```

## Example Workflow

1. **Define structure** in `conf/couchbase.yaml`:
   ```yaml
   buckets:
     main:
       scopes:
         api:
           collections:
             users: {}
             products: {}
   ```

2. **Create seed files** in `conf/seeds/`:
   - `main.api.users.json` - User data
   - `main.api.products.json` - Product data

3. **Watch it work**: The config-manager automatically creates the keyspaces and seeds the data when files are detected.
