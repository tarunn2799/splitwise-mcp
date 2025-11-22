# Splitwise MCP Server

A Model Context Protocol (MCP) server that provides AI agents with comprehensive access to Splitwise functionality for expense management, group coordination, and natural language entity resolution.

## Features

- **Complete Splitwise API Coverage**: Manage expenses, groups, friends, and comments
- **Natural Language Resolution**: Fuzzy matching for friends, groups, and categories using intelligent algorithms
- **Dual Authentication**: Support for both OAuth 2.0 and API key authentication
- **Smart Caching**: Optimized performance with intelligent data caching (24-hour TTL for static data)
- **Comprehensive Error Handling**: Clear, actionable error messages with detailed context
- **FastMCP Integration**: Built on the FastMCP framework for easy MCP server development
- **Async Operations**: Full async/await support for high performance
- **Type Safety**: Complete type hints throughout the codebase

## Installation

### From PyPI (when published)

```bash
pip install splitwise-mcp-server
```

### From Source

```bash
git clone https://github.com/yourusername/splitwise-mcp-server
cd splitwise-mcp-server
pip install -e .
```

### Requirements

- Python 3.10 or higher
- Active Splitwise account
- OAuth credentials or API key from Splitwise

## Quick Start

### 1. Configure Authentication

Copy `.env.example` to `.env` and add your Splitwise credentials:

```bash
cp .env.example .env
```

Edit `.env` with your credentials (see Authentication section below for detailed setup).

### 2. Add to MCP Configuration

Add to your MCP client configuration (e.g., Kiro's `mcp.json` or Claude Desktop's config):

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

Or reference your `.env` file:

```json
{
  "mcpServers": {
    "splitwise": {
      "command": "python",
      "args": ["-m", "splitwise_mcp_server"]
    }
  }
}
```

### 3. Start Using

The server will automatically start when your MCP client connects. Try asking your AI assistant:

- "What's my current balance on Splitwise?"
- "Create a $50 dinner expense split with John"
- "Show me my expenses from last month"

## Authentication

### OAuth 2.0 (Recommended)

OAuth 2.0 provides secure, token-based authentication with fine-grained permissions.

#### Step-by-Step OAuth Setup

1. **Register Your Application**
   
   - Go to https://secure.splitwise.com/apps
   - Click "Register your application"
   - Fill in the application details:
     - **Name**: Choose a descriptive name (e.g., "My MCP Server")
     - **Description**: Brief description of your use case
     - **Homepage URL**: Your website or `http://localhost` for personal use
     - **Callback URL**: `http://localhost:8000/callback` (or your preferred callback)
   - Click "Register"
   - **Save your Consumer Key and Consumer Secret** - you'll need these!

2. **Run the OAuth Setup Helper**

   Use the included helper script to complete the OAuth flow:

   ```bash
   python -m splitwise_mcp_server.oauth_setup
   ```

   The script will:
   - Prompt you for your Consumer Key and Consumer Secret
   - Generate an authorization URL
   - Open your browser for authorization
   - Prompt you to paste the authorization code
   - Exchange the code for an access token
   - Save everything to your `.env` file

3. **Manual OAuth Flow** (Alternative)

   If you prefer to do it manually:

   a. Get your authorization URL:
   ```
   https://secure.splitwise.com/oauth/authorize?client_id=YOUR_CONSUMER_KEY&response_type=code&redirect_uri=YOUR_CALLBACK_URL
   ```

   b. Visit the URL in your browser and authorize the application

   c. Copy the `code` parameter from the redirect URL

   d. Exchange the code for a token:
   ```bash
   curl -X POST https://secure.splitwise.com/oauth/token \
     -d "client_id=YOUR_CONSUMER_KEY" \
     -d "client_secret=YOUR_CONSUMER_SECRET" \
     -d "grant_type=authorization_code" \
     -d "code=YOUR_AUTH_CODE" \
     -d "redirect_uri=YOUR_CALLBACK_URL"
   ```

   e. Add credentials to `.env`:
   ```bash
   SPLITWISE_OAUTH_CONSUMER_KEY=your_consumer_key
   SPLITWISE_OAUTH_CONSUMER_SECRET=your_consumer_secret
   SPLITWISE_OAUTH_ACCESS_TOKEN=your_access_token
   ```

4. **Verify Authentication**

   Test your setup by running:
   ```bash
   python -c "from splitwise_mcp_server.client import SplitwiseClient; from splitwise_mcp_server.config import SplitwiseConfig; import asyncio; asyncio.run(SplitwiseClient(SplitwiseConfig.from_env()).get_current_user())"
   ```

### API Key (Alternative)

If you have a legacy API key from Splitwise:

```bash
SPLITWISE_API_KEY=your_api_key
```

**Note**: OAuth 2.0 is recommended as it provides better security and more granular permissions.

## Usage Examples

### Getting User Information

```python
# Ask your AI assistant:
"What's my Splitwise user information?"

# The assistant will use the get-current-user tool
# Returns: user ID, name, email, registration date, profile picture
```

### Creating Expenses

```python
# Simple expense between friends:
"I paid $45 for dinner with Sarah. Split it evenly."

# The assistant will:
# 1. Use resolve-friend to find Sarah's user ID
# 2. Use create-expense to create the expense
# 3. Automatically split 50/50

# Group expense:
"Create a $120 expense for groceries in my 'Roommates' group"

# The assistant will:
# 1. Use resolve-group to find the group ID
# 2. Use create-expense with the group_id
# 3. Split evenly among all group members
```

### Managing Groups

```python
# View all groups:
"Show me all my Splitwise groups"

# Create a new group:
"Create a group called 'Vacation 2024' with John and Sarah"

# Add someone to a group:
"Add Mike to my Roommates group"
```

### Querying Expenses

```python
# Recent expenses:
"Show me my expenses from the last 30 days"

# Filtered by group:
"What expenses do I have in my Roommates group?"

# Filtered by friend:
"Show me all expenses with John"
```

### Natural Language Resolution

The server includes powerful fuzzy matching for entity resolution:

```python
# Resolve friends (handles typos and partial names):
"Create an expense with Jon" # Matches "John Smith"
"Split with sara" # Matches "Sarah Johnson"

# Resolve groups:
"Add expense to roomates" # Matches "Roommates"
"Create expense in paris trip" # Matches "Paris Trip 2024"

# Resolve categories:
"Categorize as food" # Matches "Food and drink"
"Set category to utilites" # Matches "Utilities"
```

### Working with Comments

```python
# Add a comment:
"Add a comment to expense 12345: 'This was for the team lunch'"

# View comments:
"Show me comments on expense 12345"
```

## Available Tools

The server provides the following MCP tools (see [TOOLS.md](TOOLS.md) for detailed documentation):

### User Tools
- `get-current-user` - Get authenticated user information
- `get-user` - Get information about a specific user

### Expense Tools
- `create-expense` - Create a new expense with splits
- `get-expenses` - List expenses with optional filters
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

### Resolution Tools
- `resolve-friend` - Fuzzy match friend names to user IDs
- `resolve-group` - Fuzzy match group names to group IDs
- `resolve-category` - Fuzzy match category names to category IDs

### Comment Tools
- `create-comment` - Add a comment to an expense
- `get-comments` - Get all comments for an expense
- `delete-comment` - Delete a comment

### Utility Tools
- `get-categories` - Get all expense categories
- `get-currencies` - Get all supported currencies

## Configuration Options

All configuration is done via environment variables:

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `SPLITWISE_OAUTH_CONSUMER_KEY` | OAuth consumer key | - | Yes (OAuth) |
| `SPLITWISE_OAUTH_CONSUMER_SECRET` | OAuth consumer secret | - | Yes (OAuth) |
| `SPLITWISE_OAUTH_ACCESS_TOKEN` | OAuth access token | - | Yes (OAuth) |
| `SPLITWISE_API_KEY` | API key (alternative to OAuth) | - | Yes (API Key) |
| `SPLITWISE_CACHE_TTL` | Cache TTL in seconds | 86400 (24h) | No |
| `SPLITWISE_MATCH_THRESHOLD` | Fuzzy match threshold (0-100) | 70 | No |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | INFO | No |

**Note**: You must provide either OAuth credentials (consumer key, secret, and access token) OR an API key.

## Troubleshooting

### Authentication Issues

**Problem**: `Authentication failed. Check your credentials.`

**Solutions**:
- Verify your OAuth access token is correct and not expired
- Check that your consumer key and secret match your registered application
- Ensure environment variables are properly loaded (check `.env` file location)
- Try regenerating your access token using the OAuth setup helper

**Problem**: `Invalid or expired token`

**Solutions**:
- OAuth tokens may expire - regenerate using the OAuth setup helper
- Verify you're using the correct token for your environment
- Check that your Splitwise application is still active at https://secure.splitwise.com/apps

### Connection Issues

**Problem**: `Network error` or `Connection timeout`

**Solutions**:
- Check your internet connection
- Verify Splitwise API is accessible: `curl https://secure.splitwise.com/api/v3.0/test`
- Check if you're behind a proxy or firewall
- Ensure your system time is correct (affects SSL certificate validation)

### Tool Execution Issues

**Problem**: `User not found` when using resolve-friend

**Solutions**:
- Verify the person is in your Splitwise friends list
- Try using their full name or email address
- Check spelling and try variations
- Lower the match threshold: use `threshold=60` instead of default 70

**Problem**: `Group not found` when using resolve-group

**Solutions**:
- Verify the group exists in your account
- Try using the exact group name
- Check if you're still a member of the group
- Use `get-groups` to see all available groups

**Problem**: `Cannot remove user from group - balance not zero`

**Solutions**:
- Settle all expenses with the user first
- Check group balances using `get-group`
- Ensure all expenses involving the user are resolved

### Rate Limiting

**Problem**: `Rate limit exceeded. Please try again later.`

**Solutions**:
- Wait a few minutes before retrying
- Reduce the frequency of API calls
- Use caching effectively (categories and currencies are cached automatically)
- Batch operations when possible

### Data Issues

**Problem**: `Invalid currency code`

**Solutions**:
- Use `get-currencies` to see all supported currencies
- Ensure currency code is uppercase (e.g., "USD", not "usd")
- Common codes: USD, EUR, GBP, CAD, AUD, INR

**Problem**: `Invalid category ID`

**Solutions**:
- Use `get-categories` to see all available categories
- Use `resolve-category` for fuzzy matching (e.g., "food" → "Food and drink")
- Category IDs are integers, not strings

### MCP Configuration Issues

**Problem**: Server not appearing in MCP client

**Solutions**:
- Verify `mcp.json` syntax is correct (valid JSON)
- Check that Python is in your PATH
- Ensure the package is installed: `pip list | grep splitwise-mcp-server`
- Restart your MCP client after configuration changes
- Check MCP client logs for error messages

**Problem**: Environment variables not loading

**Solutions**:
- Specify env variables directly in `mcp.json` config
- Ensure `.env` file is in the correct location
- Use absolute paths for environment variable files
- Check file permissions on `.env` file

### Debugging

Enable debug logging to see detailed information:

```bash
# In your .env file:
LOG_LEVEL=DEBUG
```

Or in your MCP configuration:

```json
{
  "mcpServers": {
    "splitwise": {
      "command": "python",
      "args": ["-m", "splitwise_mcp_server"],
      "env": {
        "SPLITWISE_OAUTH_ACCESS_TOKEN": "your_token",
        "LOG_LEVEL": "DEBUG"
      }
    }
  }
}
```

Check logs for:
- API request/response details
- Authentication header generation
- Cache hit/miss information
- Error stack traces

### Getting Help

If you're still experiencing issues:

1. Check the [GitHub Issues](https://github.com/yourusername/splitwise-mcp-server/issues) for similar problems
2. Review the [Splitwise API Documentation](https://dev.splitwise.com/)
3. Enable debug logging and include relevant logs when reporting issues
4. Provide your Python version, OS, and MCP client information

## Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/yourusername/splitwise-mcp-server
cd splitwise-mcp-server

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install with dev dependencies
pip install -e ".[dev]"
```

### Run Tests

```bash
pytest
```

### Project Structure

```
splitwise-mcp-server/
├── src/
│   └── splitwise_mcp_server/
│       ├── __init__.py
│       ├── __main__.py
│       ├── auth.py          # Authentication handlers
│       ├── cache.py         # Caching layer
│       ├── client.py        # Splitwise API client
│       ├── config.py        # Configuration management
│       ├── errors.py        # Error handling
│       ├── models.py        # Data models
│       ├── resolver.py      # Entity resolution
│       └── server.py        # FastMCP server and tools
├── tests/                   # Test suite
├── .env.example            # Example environment configuration
├── .gitignore              # Git ignore rules
├── pyproject.toml          # Project metadata and dependencies
└── README.md               # This file
```

## License

MIT License - see LICENSE file for details

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues and questions:
- GitHub Issues: https://github.com/yourusername/splitwise-mcp-server/issues
- Splitwise API Documentation: https://dev.splitwise.com/

## Acknowledgments

Built with [FastMCP](https://github.com/jlowin/fastmcp) and powered by the [Splitwise API](https://dev.splitwise.com/).
