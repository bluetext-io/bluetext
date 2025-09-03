# Bluetext

A comprehensive development framework built on Polytope, designed to accelerate enterprise-grade application development with intelligent coding assistance.

## Prerequisites

### Update Existing Installation

To install the newest version of Polytope or update it, run:

```bash
curl -s https://polytope.com/install.sh | sh -s -- --edge
```

### Making PT Tool Available (Pre-release Users)

If you're on a Polytope pre-release and want to make the `pt` tool available from your command line:

**To enable for current session only:**
```bash
export PATH="~/.local/bin/polytope:$PATH" && source ~/.zshrc
```

**To enable permanently:**
```bash
echo 'export PATH="~/.local/bin/polytope:$PATH"' >> ~/.zshrc && source ~/.zshrc
```

## Setup Instructions

### Step 1: Start Polytope MCP Server

Execute the following command while in the `bluetext directory` to run the Polytope MCP server:

```bash
pt run --mcp
```

### Step 2: Port Forwarding (Required)

Due to a known issue in Cline, you must run this command in a separate terminal to properly forward traffic:

```bash
sudo socat TCP-LISTEN:80,fork TCP:localhost:81883
```

**Note:** Keep this terminal session running while using Bluetext with Cline.

### Step 3: Configure Cline Integration

To integrate with Cline, add the following configuration to your Cline MCP config file:

```json
{
  "mcpServers": {
    "polytope": {
      "type": "streamableHttp",
      "url": "http://localhost/mcp",
      "alwaysAllow": ["tool3"],
      "disabled": false
    }
  }
}
```

## Start using bluetext

Once the setup is complete, you can begin using Bluetext through Cline or other MCP-compatible tools.

To test if setup has been completed correctly, try running a sample promot. For example, run:
'Use polytope to build a website with a contact form and save its contents'