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

### 2. Configure Port

Configure the correct port that needs to be exposed in the `cmd` field in `polytope.yml` in the module directory. The format is:

```
http <service-name>:<port>
```

For example: `http api:3030` or `http backend:8000`

### 3. Restart the Module

After setting the secret and configuring the port values, restart the module to apply the changes:

```bash
pt run ngrok
```
