# Splitwise MCP Server - Kiro CLI Setup Guide

This guide walks you through setting up and testing the Splitwise MCP Server with Kiro CLI.

## Prerequisites

- Python 3.10 or higher
- Active Splitwise account
- Kiro CLI installed

## Step-by-Step Setup

### Step 1: Get Splitwise OAuth Credentials

1. Go to https://secure.splitwise.com/apps
2. Click "Register your application"
3. Fill in the application details:
   - **Name**: "Kiro MCP Test" (or your preferred name)
   - **Description**: "Testing Splitwise MCP server with Kiro"
   - **Homepage URL**: `http://localhost` (for personal use)
   - **Callback URL**: `http://localhost:8000/callback`
4. Click "Register"
5. **Save your Consumer Key and Consumer Secret** - you'll need these next!

### Step 2: Run OAuth Setup Helper

From your project directory, run:

```bash
python -m splitwise_mcp_server.oauth_setup
```

The helper will:
1. Prompt you for your Consumer Key and Consumer Secret
2. Open your browser for authorization
3. Ask you to paste the authorization code from the redirect URL
4. Exchange the code for an access token
5. Save everything to `.env` file

**Example interaction:**
```
Enter your Consumer Key: YOUR_CONSUMER_KEY
Enter your Consumer Secret: YOUR_CONSUMER_SECRET
[Browser opens for authorization]
Paste the redirect URL or authorization code: YOUR_AUTH_CODE
✓ Access token obtained successfully
✓ Credentials saved to: /path/to/project/.env
✓ Token is valid!
  Authenticated as: Your Name
```

### Step 3: Configure MCP Server in Kiro

Create or update `.kiro/settings/mcp.json`:

```bash
mkdir -p .kiro/settings
```

Add the following configuration (replace with your actual credentials from `.env`):

```json
{
  "mcpServers": {
    "splitwise": {
      "command": "python",
      "args": ["-m", "splitwise_mcp_server"],
      "env": {
        "SPLITWISE_OAUTH_CONSUMER_KEY": "your_consumer_key_here",
        "SPLITWISE_OAUTH_CONSUMER_SECRET": "your_consumer_secret_here",
        "SPLITWISE_OAUTH_ACCESS_TOKEN": "your_access_token_here",
        "LOG_LEVEL": "INFO"
      },
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

**Note:** You can copy the values from your `.env` file.

### Step 4: Test the Configuration

#### Test 1: Verify API Connection

```bash
python << 'EOF'
import asyncio
from splitwise_mcp_server.config import SplitwiseConfig
from splitwise_mcp_server.auth import OAuth2Handler
from splitwise_mcp_server.client import SplitwiseClient

async def test():
    config = SplitwiseConfig.from_env()
    auth = OAuth2Handler(
        consumer_key=config.oauth_consumer_key,
        consumer_secret=config.oauth_consumer_secret,
        access_token=config.oauth_access_token
    )
    
    async with SplitwiseClient(auth) as client:
        response = await client.get_current_user()
        user = response['user']
        print(f"✓ Connected as: {user['first_name']} {user['last_name']}")
        print(f"✓ Email: {user['email']}")
        print(f"✓ User ID: {user['id']}")

asyncio.run(test())
EOF
```

Expected output:
```
✓ Connected as: Your Name
✓ Email: your.email@example.com
✓ User ID: 12345678
```

#### Test 2: Test Multiple API Endpoints

```bash
python << 'EOF'
import asyncio
from splitwise_mcp_server.config import SplitwiseConfig
from splitwise_mcp_server.auth import OAuth2Handler
from splitwise_mcp_server.client import SplitwiseClient

async def test():
    config = SplitwiseConfig.from_env()
    auth = OAuth2Handler(
        consumer_key=config.oauth_consumer_key,
        consumer_secret=config.oauth_consumer_secret,
        access_token=config.oauth_access_token
    )
    
    async with SplitwiseClient(auth) as client:
        print("Testing API endpoints:\n")
        
        user_response = await client.get_current_user()
        user = user_response['user']
        print(f"1. ✓ Get Current User: {user['first_name']} {user['last_name']}")
        
        friends = await client.get_friends()
        print(f"2. ✓ Get Friends: Found {len(friends)} friends")
        
        groups = await client.get_groups()
        print(f"3. ✓ Get Groups: Found {len(groups)} groups")
        
        categories = await client.get_categories()
        print(f"4. ✓ Get Categories: Found {len(categories)} categories")
        
        currencies = await client.get_currencies()
        print(f"5. ✓ Get Currencies: Found {len(currencies)} currencies")
        
        print("\n✓ All API tests passed!")

asyncio.run(test())
EOF
```

### Step 5: Start the MCP Server

You can start the server manually to test:

```bash
python -m splitwise_mcp_server
```

The server will start and wait for MCP client connections. You should see:
```
INFO:splitwise_mcp_server.server:FastMCP server created
INFO:splitwise_mcp_server.server:All tools registered successfully
```

Press `Ctrl+C` to stop the server.

### Step 6: Use with Kiro CLI

Once configured, Kiro will automatically start the MCP server when needed. You can now use Splitwise tools in your Kiro conversations:

**Example queries:**
- "What's my current balance on Splitwise?"
- "Show me my Splitwise friends"
- "List my Splitwise groups"
- "What expense categories are available?"
- "Create a $50 dinner expense split with John"

### Step 7: Verify MCP Server in Kiro

1. Open Kiro CLI
2. The MCP server should automatically connect
3. Check the MCP Server view in Kiro to see if "splitwise" is listed and connected
4. Try asking: "What's my Splitwise user information?"

## Available Tools

The server provides 20+ MCP tools organized into categories:

### User Tools
- `get-current-user` - Get authenticated user information
- `get-user` - Get information about a specific user

### Expense Tools
- `create-expense` - Create a new expense with splits
- `get-expenses` - List expenses with filters
- `get-expense` - Get detailed expense information
- `update-expense` - Update an existing expense
- `delete-expense` - Delete an expense

### Group Tools
- `get-groups` - List all groups
- `get-group` - Get detailed group information
- `create-group` - Create a new group
- `delete-group` - Delete a group
- `add-user-to-group` - Add a user to a group
- `remove-user-from-group` - Remove a user from a group

### Friend Tools
- `get-friends` - List all friends
- `get-friend` - Get detailed friend information

### Resolution Tools (Fuzzy Matching)
- `resolve-friend` - Match friend names to user IDs
- `resolve-group` - Match group names to group IDs
- `resolve-category` - Match category names to category IDs

### Comment Tools
- `create-comment` - Add a comment to an expense
- `get-comments` - Get all comments for an expense
- `delete-comment` - Delete a comment

### Utility Tools
- `get-categories` - Get all expense categories
- `get-currencies` - Get all supported currencies

See [TOOLS.md](TOOLS.md) for detailed documentation of each tool.

## Troubleshooting

### Issue: "Authentication failed"

**Solution:**
1. Verify your `.env` file has the correct credentials
2. Check that the credentials in `.kiro/settings/mcp.json` match your `.env` file
3. Try regenerating your access token using the OAuth setup helper

### Issue: "Module not found"

**Solution:**
1. Ensure you're in the project directory
2. Install the package: `pip install -e .`
3. Verify installation: `pip show splitwise-mcp-server`

### Issue: "MCP server not connecting in Kiro"

**Solution:**
1. Check `.kiro/settings/mcp.json` syntax is valid JSON
2. Verify Python is in your PATH: `which python`
3. Restart Kiro CLI
4. Check Kiro logs for error messages

### Issue: "Rate limit exceeded"

**Solution:**
1. Wait a few minutes before retrying
2. The server uses caching to minimize API calls
3. Categories and currencies are cached for 24 hours

## Advanced Configuration

### Custom Cache TTL

Adjust cache duration in your MCP config:

```json
{
  "mcpServers": {
    "splitwise": {
      "env": {
        "SPLITWISE_CACHE_TTL": "43200"
      }
    }
  }
}
```

### Custom Fuzzy Match Threshold

Adjust fuzzy matching sensitivity (0-100, default 70):

```json
{
  "mcpServers": {
    "splitwise": {
      "env": {
        "SPLITWISE_MATCH_THRESHOLD": "80"
      }
    }
  }
}
```

### Debug Logging

Enable detailed logging:

```json
{
  "mcpServers": {
    "splitwise": {
      "env": {
        "LOG_LEVEL": "DEBUG"
      }
    }
  }
}
```

## Next Steps

1. Try creating expenses with natural language
2. Use fuzzy matching to resolve friends and groups
3. Explore group management features
4. Set up automated expense tracking workflows

For more information, see:
- [README.md](README.md) - Full documentation
- [TOOLS.md](TOOLS.md) - Detailed tool reference
- [Splitwise API Docs](https://dev.splitwise.com/) - Official API documentation

## Support

If you encounter issues:
1. Check this guide's troubleshooting section
2. Review the [README.md](README.md) troubleshooting section
3. Enable debug logging to see detailed error messages
4. Check GitHub Issues for similar problems
