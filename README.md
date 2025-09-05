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

## MCP Server Setup Instructions

### Step 1: Start Polytope MCP Server

Execute the following command while in the `bluetext directory` to run the Polytope MCP server:

```bash
pt run --mcp
```

### Step 2: Connect Polytope to MCP Server

Before connecting Polytope to the MCP server, you must first install Bun:

```bash
curl -fsSL https://bun.sh/install | bash
```

Once bun is installed, launch the MCP inspector to establish the connection:

```bash
bun x @modelcontextprotocol/inspector
```
Sometimes this will not automatically establish the connection, in which case click "connect" on the MCP.

## Using Polytope with Claude

Add Polytope as a local MCP server to Claude:

```bash
claude mcp add local-mcp -t http localhost:31338/mcp
```

To test if claude has successfully connected to the server, run the following command:

```bash
claude mp list
```

lastly, open claude in the project folder under the bluetext directory to start generating!


## Using Polytope with Cline

Due to a known issue in Cline, you must run this command in a separate terminal to properly forward traffic:

```bash
sudo socat TCP-LISTEN:80,fork TCP:localhost:31338
```
**Note:** Keep this terminal session running while using Bluetext with Cline.

### Configure Cline Integration

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

Once the setup is complete, you can begin using Bluetext through Claude, Clein, or other MCP-compatible tools.
To test if setup has been completed correctly, try running a sample promot. For example, run:
'Use polytope to build a website with a contact form and save its contents'

**note** Before running a new project, make sure co clear and inspect the tools from the MCP