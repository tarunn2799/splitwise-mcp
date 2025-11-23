# Setup Guide

This guide covers authentication and configuration for the Splitwise MCP Server.

## Authentication

You need to authenticate with Splitwise to use this server. We recommend **OAuth 2.0** for the best security and experience.

### Option 1: OAuth 2.0 (Recommended)

This method uses a secure token to access your account.

#### 1. Register Your Application
1. Go to [Splitwise Apps](https://secure.splitwise.com/apps).
2. Click **Register your application**.
3. Fill in the details:
   - **Name**: `Splitwise MCP` (or similar)
   - **Homepage URL**: `http://localhost`
   - **Callback URL**: `http://localhost:8000/callback`
4. Click **Register**.
5. Copy your **Consumer Key** and **Consumer Secret**.

#### 2. Generate Tokens
Run the included setup script:

```bash
python -m splitwise_mcp_server.oauth_setup
```

Follow the prompts to paste your keys and authorize the app in your browser. The script will automatically save your credentials to a `.env` file.

### Option 2: API Key (Legacy)

If you already have an API key:
1. Create a `.env` file in the project root.
2. Add: `SPLITWISE_API_KEY=your_api_key_here`

---

## MCP Configuration

Configure your MCP client (like Claude Desktop or Kiro) to use the server.

### Standard Configuration

Add this to your `mcp.json` config file:

```json
{
  "mcpServers": {
    "splitwise": {
      "command": "python",
      "args": ["-m", "splitwise_mcp_server"],
      "env": {
        "SPLITWISE_OAUTH_ACCESS_TOKEN": "your_token_here" 
      }
    }
  }
}
```
*(Note: If you used the setup script, the token is in your `.env` file. You can reference that file instead if your client supports it, or copy the token here.)*

### Using a Virtual Environment (venv/conda)

**Important**: If you installed the package in a virtual environment (like `venv` or `conda`), you **must** use the absolute path to the python executable in that environment.

**Example:**

```json
{
  "mcpServers": {
    "splitwise": {
      "command": "/Users/username/projects/splitwise-mcp/venv/bin/python", 
      "args": ["-m", "splitwise_mcp_server"]
    }
  }
}
```

**How to find your python path:**
Activate your environment and run:
- **Mac/Linux**: `which python`
- **Windows**: `where python`
