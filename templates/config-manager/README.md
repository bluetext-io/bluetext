# Config Manager

Manages Couchbase buckets/scopes/collections and Redpanda topics with continuous monitoring.

## How It Works

The config-manager runs continuously, monitoring the `conf` directory for changes. When configuration files are added or modified, it automatically processes them to ensure resources are created and configured correctly.

## Couchbase Configuration

Define your Couchbase resources in `conf/couchbase.yaml`:

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

The config-manager will automatically create buckets, scopes, and collections based on this configuration.

## Redpanda Configuration

Define your Redpanda topics in `conf/redpanda.yaml`:

```yaml
topics:
  events:
    partitions: 3
    replication_factor: 1
```

## Directory Structure

```
conf/
├── config.yaml          # Environment configuration
├── couchbase.yaml       # Couchbase resource definitions (optional)
└── redpanda.yaml        # Redpanda topic definitions (optional)
```

## Automatic Processing

The config-manager watches `conf/` and will automatically:
1. Process `couchbase.yaml` to create buckets/scopes/collections
2. Process `redpanda.yaml` to create topics
3. Continuously monitor for changes and apply updates
