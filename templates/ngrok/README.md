# Ngrok

This module sets up an ngrok tunnel service for exposing localhost APIs publicly.

## First-Time Setup

### 1. Configure Authentication Token

If this is the first time using the ngrok module, you must set the `ngrok-auth-token` polytope secret:

```bash
pt secrets set ngrok-auth-token YOUR_AUTH_TOKEN
```

You can verify the secret exists using:

```bash
pt secrets list
```

Get your authentication token from: https://dashboard.ngrok.com/get-started/your-authtoken

### 2. Configure Services to Tunnel

Edit the `conf/ngrok.yml` file to define which services need to be tunnelled. Add or modify entries in the `endpoints` section:

```yaml
endpoints:
  - name: api
    description: API endpoint for example service
    upstream:
      url: 3000
```

Each endpoint entry specifies:
- `name`: A unique identifier for the tunnel
- `description`: Optional description of the service
- `upstream.url`: The port number or service name to tunnel to

You can add multiple endpoints to tunnel multiple services simultaneously.

### 3. Restart the Module

After setting the secret and configuring the services in `ngrok.yml`, restart the module to apply the changes:

```bash
pt run ngrok
```
