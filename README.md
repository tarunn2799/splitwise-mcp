# Splitwise MCP Server

A Model Context Protocol (MCP) server for [Splitwise](https://www.splitwise.com/), enabling AI agents to manage expenses, groups, and friends with natural language.

## Features

- **Full API Access**: Manage expenses, groups, friends, and comments.
- **Natural Language Resolution**: Fuzzy matching for names ("John" -> "John Smith") and groups.
- **Dual Auth**: Supports both OAuth 2.0 (recommended) and API Keys.
- **Smart Caching**: Optimizes performance for static data like categories and currencies.

## Installation

```bash
# From PyPI (when published)
pip install splitwise-mcp-server

# From Source
git clone https://github.com/tarunn2799/splitwise-mcp-server
cd splitwise-mcp-server
pip install -e .
```

## Configuration

See [SETUP.md](SETUP.md) for detailed authentication and configuration instructions.

### Quick Config
Run the included setup script:
```
python -m splitwise_mcp_server.oauth_setup
```

Use the keys provided there, and add all three to your `mcp.json`:

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

> **Get your Auth Keys**
> You can get your Consumer Key and Secret by registering an app at [https://secure.splitwise.com/apps](https://secure.splitwise.com/apps).

> **IMPORTANT:** Using a Virtual Environment?
> If you installed the package in a `venv` or Conda environment, you must use the **absolute path** to the python executable in your config.
>
> ```json
> "command": "/absolute/path/to/venv/bin/python"
> ```
> See [SETUP.md](SETUP.md#using-a-virtual-environment-venvconda) for details.

## Usage

The server enables natural language interactions with your Splitwise data.

**Examples:**
- "What's my current balance?"
- "Split a $50 dinner with Sarah."
- "Use the receipt I uploaded to split the dinner between Manav and me."
- "Show me expenses from last month."
- "Create a group called 'Ski Trip' with Mike."

## Tools

See [TOOLS.md](TOOLS.md) for detailed documentation.

### User Tools
- `get-current-user`: Get authenticated user information
- `get-user`: Get information about a specific user

### Expense Tools
- `create-expense`: Create a new expense with splits
- `get-expenses`: List expenses with optional filters
- `get-expense`: Get detailed expense information
- `update-expense`: Update an existing expense
- `delete-expense`: Delete an expense

### Group Tools
- `get-groups`: List all groups
- `get-group`: Get detailed group information
- `create-group`: Create a new group
- `delete-group`: Delete a group
- `add-user-to-group`: Add a user to a group
- `remove-user-from-group`: Remove a user from a group

### Friend Tools
- `get-friends`: List all friends
- `get-friend`: Get detailed friend information

### Resolution Tools
- `resolve-friend`: Fuzzy match friend names to user IDs
- `resolve-group`: Fuzzy match group names to group IDs
- `resolve-category`: Fuzzy match category names to category IDs

### Comment Tools
- `create-comment`: Add a comment to an expense
- `get-comments`: Get all comments for an expense
- `delete-comment`: Delete a comment

### Utility Tools
- `get-categories`: Get all expense categories
- `get-currencies`: Get all supported currencies

### Arithmetic Tools
- `add`: Add multiple numbers
- `subtract`: Subtract numbers
- `multiply`: Multiply numbers
- `divide`: Divide numbers
- `modulo`: Calculate remainder

## Development

```bash
# Setup
git clone https://github.com/tarunn2799/splitwise-mcp-server
cd splitwise-mcp-server
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"

# Test
pytest
```

## License

MIT License. See [LICENSE](LICENSE) for details.
