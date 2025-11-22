# Design Document

## Overview

The Splitwise MCP Server is a Python-based Model Context Protocol server that provides comprehensive access to Splitwise functionality through a set of well-defined tools. The server will be built using the FastMCP framework, which simplifies MCP server development with decorators and automatic tool registration. The architecture emphasizes modularity, security, and ease of use, with natural language entity resolution as a key differentiator.

**Important**: All API endpoints and data structures are based on official Splitwise API documentation retrieved via Context7. No API usage is assumed or hallucinated. If a feature is not documented in the official API, it will not be implemented.

## MCP Best Practices

This implementation follows the official MCP best practices to ensure reliability, usability, and maintainability:

### 1. Tool Design Best Practices

**Single Responsibility Principle**
- Each tool performs one specific action (e.g., `create-expense`, `get-groups`)
- Tools are focused and don't combine multiple operations
- Clear separation between read and write operations

**Descriptive Naming**
- Tool names use kebab-case (e.g., `get-current-user`, `resolve-friend`)
- Names clearly indicate the action and resource (verb-noun pattern)
- Consistent naming conventions across all tools

**Comprehensive Documentation**
- Every tool includes detailed docstrings with purpose, parameters, and return values
- Parameter descriptions include types, constraints, and examples
- Return value schemas are documented with example responses

**Input Validation**
- All required parameters are explicitly marked
- Optional parameters have sensible defaults
- Type hints are used throughout for clarity
- Input validation happens before API calls

### 2. Error Handling Best Practices

**Structured Error Responses**
- All errors return consistent JSON structure with `error_type`, `message`, `status_code`, and `details`
- Error messages are human-readable and actionable
- Include context about what went wrong and how to fix it

**Graceful Degradation**
- Network failures are caught and reported clearly
- API rate limits are handled with retry guidance
- Partial failures in batch operations are reported individually

**Error Categories**
- Authentication errors (401) - credential issues
- Authorization errors (403) - permission issues
- Not found errors (404) - invalid IDs
- Validation errors (400) - invalid input
- Rate limit errors (429) - too many requests
- Server errors (500+) - API or network issues

### 3. State Management Best Practices

**Stateless Design**
- Each tool invocation is independent
- No shared mutable state between requests
- Authentication credentials loaded from environment

**Caching Strategy**
- Cache static data (categories, currencies) for 24 hours
- Cache user data (friends, groups) for 5 minutes
- Invalidate cache on write operations
- TTL-based expiration to prevent stale data

**Connection Management**
- Use connection pooling for HTTP requests
- Reuse connections across multiple tool invocations
- Proper cleanup on server shutdown

### 4. Security Best Practices

**Credential Management**
- Never log or expose authentication tokens
- Store credentials in environment variables only
- Support both OAuth and API key authentication
- Clear documentation on secure credential storage

**Input Sanitization**
- Validate all user inputs before API calls
- Escape special characters in strings
- Validate numeric ranges and formats
- Prevent injection attacks

**HTTPS Only**
- All API requests use HTTPS
- SSL certificate verification enabled
- No fallback to HTTP

### 5. Performance Best Practices

**Async Operations**
- All I/O operations are async
- Support concurrent tool invocations
- Use asyncio for parallel requests when appropriate

**Efficient Data Transfer**
- Request only needed fields from API
- Use pagination for large result sets
- Implement reasonable default limits

**Resource Management**
- Proper cleanup of HTTP connections
- Memory-efficient caching with TTL
- Avoid unnecessary API calls through caching

### 6. Usability Best Practices

**Natural Language Support**
- Fuzzy matching for entity resolution
- Handle typos and variations in names
- Return multiple matches with confidence scores

**Helpful Defaults**
- Sensible default values for optional parameters
- Current timestamp for date fields
- USD as default currency
- Reasonable pagination limits

**Rich Responses**
- Include relevant context in responses
- Provide IDs and names for referenced entities
- Include balance information where relevant

### 7. Testing Best Practices

**Comprehensive Test Coverage**
- Unit tests for all components
- Integration tests for end-to-end flows
- Mock external API calls in unit tests
- Test error scenarios and edge cases

**Test Organization**
- Separate test files for each component
- Use fixtures for common test data
- Clear test names describing what is tested

### 8. Documentation Best Practices

**README Documentation**
- Quick start guide with minimal steps
- Complete setup instructions for OAuth
- Example usage for common scenarios
- Troubleshooting section for common issues

**Code Documentation**
- Docstrings for all public functions
- Type hints throughout codebase
- Inline comments for complex logic
- Architecture diagrams for clarity

**API Documentation**
- Tool reference with all parameters
- Example requests and responses
- Error codes and meanings
- Rate limit information

## Architecture

### High-Level Architecture

```
┌─────────────────┐
│   AI Agent      │
│   (e.g., Kiro)  │
└────────┬────────┘
         │ MCP Protocol
         │
┌────────▼────────────────────────────────────┐
│         Splitwise MCP Server                │
│  ┌──────────────────────────────────────┐  │
│  │     Tool Layer (FastMCP)             │  │
│  │  - Expense Tools                     │  │
│  │  - Group Tools                       │  │
│  │  - Friend Tools                      │  │
│  │  - Resolution Tools                  │  │
│  │  - Utility Tools                     │  │
│  └──────────────┬───────────────────────┘  │
│                 │                           │
│  ┌──────────────▼───────────────────────┐  │
│  │     Service Layer                    │  │
│  │  - SplitwiseClient                   │  │
│  │  - EntityResolver                    │  │
│  │  - CacheManager                      │  │
│  └──────────────┬───────────────────────┘  │
│                 │                           │
│  ┌──────────────▼───────────────────────┐  │
│  │     Authentication Layer             │  │
│  │  - OAuth2Handler                     │  │
│  │  - APIKeyHandler                     │  │
│  └──────────────────────────────────────┘  │
└────────────────┬────────────────────────────┘
                 │ HTTPS
                 │
┌────────────────▼────────────────┐
│     Splitwise REST API          │
│  https://secure.splitwise.com   │
└─────────────────────────────────┘
```

### Technology Stack

- **Language**: Python 3.10+
- **MCP Framework**: FastMCP (for simplified MCP server development)
- **HTTP Client**: httpx (async HTTP client with connection pooling)
- **Authentication**: OAuth2 via requests-oauthlib or custom implementation
- **Configuration**: python-dotenv for environment variable management
- **Fuzzy Matching**: rapidfuzz for natural language entity resolution
- **Caching**: In-memory dictionary with TTL for categories and currencies

## Components and Interfaces

### 1. Authentication Layer

#### OAuth2Handler
Manages OAuth 2.0 authentication flow for Splitwise.

```python
class OAuth2Handler:
    """Handles OAuth 2.0 authentication with Splitwise."""
    
    def __init__(self, consumer_key: str, consumer_secret: str):
        """Initialize with OAuth credentials."""
        
    def get_authorization_url(self) -> str:
        """Generate authorization URL for user consent."""
        
    def exchange_code_for_token(self, code: str) -> dict:
        """Exchange authorization code for access token."""
        
    def get_access_token(self) -> str:
        """Retrieve current access token."""
```

#### APIKeyHandler
Alternative authentication using API key and secret.

```python
class APIKeyHandler:
    """Handles API Key authentication with Splitwise."""
    
    def __init__(self, api_key: str):
        """Initialize with API key."""
        
    def get_auth_header(self) -> dict:
        """Generate authentication header for requests."""
```

### 2. Service Layer

#### SplitwiseClient
Core client for interacting with Splitwise API.

```python
class SplitwiseClient:
    """Main client for Splitwise API interactions."""
    
    BASE_URL = "https://secure.splitwise.com/api/v3.0"
    
    def __init__(self, auth_handler: Union[OAuth2Handler, APIKeyHandler]):
        """Initialize with authentication handler."""
        
    async def get(self, endpoint: str, params: dict = None) -> dict:
        """Make GET request to Splitwise API."""
        
    async def post(self, endpoint: str, data: dict = None) -> dict:
        """Make POST request to Splitwise API."""
        
    async def put(self, endpoint: str, data: dict = None) -> dict:
        """Make PUT request to Splitwise API."""
        
    # User endpoints
    async def get_current_user(self) -> dict:
        """Get current authenticated user information."""
        
    async def get_user(self, user_id: int) -> dict:
        """Get information about a specific user."""
        
    # Expense endpoints
    async def get_expenses(self, **filters) -> dict:
        """Get list of expenses with optional filters."""
        
    async def get_expense(self, expense_id: int) -> dict:
        """Get detailed information about an expense."""
        
    async def create_expense(self, expense_data: dict) -> dict:
        """Create a new expense."""
        
    async def update_expense(self, expense_id: int, expense_data: dict) -> dict:
        """Update an existing expense."""
        
    async def delete_expense(self, expense_id: int) -> dict:
        """Delete an expense."""
        
    # Group endpoints
    async def get_groups(self) -> dict:
        """Get all groups for current user."""
        
    async def get_group(self, group_id: int) -> dict:
        """Get detailed information about a group."""
        
    async def create_group(self, group_data: dict) -> dict:
        """Create a new group."""
        
    async def delete_group(self, group_id: int) -> dict:
        """Delete a group."""
        
    async def add_user_to_group(self, group_id: int, user_id: int) -> dict:
        """Add a user to a group."""
        
    async def remove_user_from_group(self, group_id: int, user_id: int) -> dict:
        """Remove a user from a group."""
        
    # Friend endpoints
    async def get_friends(self) -> dict:
        """Get all friends for current user."""
        
    async def get_friend(self, user_id: int) -> dict:
        """Get detailed information about a friend."""
        
    # Comment endpoints
    async def get_comments(self, expense_id: int) -> dict:
        """Get comments for an expense."""
        
    async def create_comment(self, expense_id: int, content: str) -> dict:
        """Create a comment on an expense."""
        
    async def delete_comment(self, comment_id: int) -> dict:
        """Delete a comment."""
        
    # Utility endpoints
    async def get_categories(self) -> dict:
        """Get all supported expense categories."""
        
    async def get_currencies(self) -> dict:
        """Get all supported currencies."""
```

#### EntityResolver
Provides natural language resolution for Splitwise entities.

```python
class EntityResolver:
    """Resolves natural language references to Splitwise entities."""
    
    def __init__(self, client: SplitwiseClient):
        """Initialize with Splitwise client."""
        
    async def resolve_friend(self, query: str, threshold: int = 70) -> list:
        """
        Resolve friend name to user ID(s).
        
        Args:
            query: Natural language query (e.g., "John", "john smith")
            threshold: Minimum fuzzy match score (0-100)
            
        Returns:
            List of matching friends with scores
        """
        
    async def resolve_group(self, query: str, threshold: int = 70) -> list:
        """
        Resolve group name to group ID(s).
        
        Args:
            query: Natural language query (e.g., "roommates", "trip to paris")
            threshold: Minimum fuzzy match score (0-100)
            
        Returns:
            List of matching groups with scores
        """
        
    async def resolve_category(self, query: str, threshold: int = 70) -> list:
        """
        Resolve category name to category ID(s).
        
        Args:
            query: Natural language query (e.g., "food", "groceries")
            threshold: Minimum fuzzy match score (0-100)
            
        Returns:
            List of matching categories with scores
        """
        
    def _fuzzy_match(self, query: str, candidates: list, key_func) -> list:
        """Internal fuzzy matching logic using rapidfuzz."""
```

#### CacheManager
Manages caching for categories and currencies to reduce API calls.

```python
class CacheManager:
    """Manages caching of frequently accessed data."""
    
    def __init__(self, ttl_seconds: int = 86400):  # 24 hours default
        """Initialize cache with TTL."""
        
    def get(self, key: str) -> Optional[Any]:
        """Retrieve cached value if not expired."""
        
    def set(self, key: str, value: Any):
        """Store value in cache with timestamp."""
        
    def clear(self):
        """Clear all cached data."""
```

### 3. Tool Layer (FastMCP)

The tool layer exposes MCP tools using FastMCP decorators. Each tool corresponds to a specific Splitwise operation.

#### User Tools

```python
@mcp.tool()
async def get_current_user() -> dict:
    """Get information about the currently authenticated user."""
    
@mcp.tool()
async def get_user(user_id: int) -> dict:
    """Get information about a specific user by ID."""
```

#### Expense Tools

```python
@mcp.tool()
async def create_expense(
    cost: str,
    description: str,
    group_id: int = 0,
    currency_code: str = "USD",
    date: Optional[str] = None,
    category_id: Optional[int] = None,
    users: list[dict] = None
) -> dict:
    """
    Create a new expense in Splitwise.
    
    Args:
        cost: Amount as string with 2 decimal places (e.g., "25.50")
        description: Short description of the expense
        group_id: Group ID (0 for non-group expense)
        currency_code: Currency code (default: USD)
        date: ISO 8601 datetime string (default: now)
        category_id: Category ID from get_categories
        users: List of user split information
    """

@mcp.tool()
async def get_expenses(
    group_id: Optional[int] = None,
    friend_id: Optional[int] = None,
    dated_after: Optional[str] = None,
    dated_before: Optional[str] = None,
    limit: int = 20,
    offset: int = 0
) -> dict:
    """Get list of expenses with optional filters."""

@mcp.tool()
async def get_expense(expense_id: int) -> dict:
    """Get detailed information about a specific expense."""

@mcp.tool()
async def update_expense(
    expense_id: int,
    cost: Optional[str] = None,
    description: Optional[str] = None,
    date: Optional[str] = None,
    category_id: Optional[int] = None,
    users: Optional[list[dict]] = None
) -> dict:
    """Update an existing expense."""

@mcp.tool()
async def delete_expense(expense_id: int) -> dict:
    """Delete an expense."""
```

#### Group Tools

```python
@mcp.tool()
async def get_groups() -> dict:
    """Get all groups for the current user."""

@mcp.tool()
async def get_group(group_id: int) -> dict:
    """Get detailed information about a specific group."""

@mcp.tool()
async def create_group(
    name: str,
    group_type: str = "other",
    simplify_by_default: bool = True,
    users: Optional[list[dict]] = None
) -> dict:
    """
    Create a new group.
    
    Args:
        name: Group name
        group_type: Type (home, trip, couple, other)
        simplify_by_default: Enable debt simplification
        users: List of initial members
    """

@mcp.tool()
async def delete_group(group_id: int) -> dict:
    """Delete a group."""

@mcp.tool()
async def add_user_to_group(group_id: int, user_id: int) -> dict:
    """Add a user to a group."""

@mcp.tool()
async def remove_user_from_group(group_id: int, user_id: int) -> dict:
    """Remove a user from a group (requires zero balance)."""
```

#### Friend Tools

```python
@mcp.tool()
async def get_friends() -> dict:
    """Get all friends for the current user."""

@mcp.tool()
async def get_friend(user_id: int) -> dict:
    """Get detailed information about a specific friend."""
```

#### Resolution Tools

```python
@mcp.tool()
async def resolve_friend(query: str, threshold: int = 70) -> list:
    """
    Resolve a natural language friend reference to user ID(s).
    
    Args:
        query: Friend name or partial name (e.g., "John", "john smith")
        threshold: Minimum match score 0-100 (default: 70)
        
    Returns:
        List of matching friends with IDs, names, and match scores
    """

@mcp.tool()
async def resolve_group(query: str, threshold: int = 70) -> list:
    """
    Resolve a natural language group reference to group ID(s).
    
    Args:
        query: Group name or partial name (e.g., "roommates", "paris trip")
        threshold: Minimum match score 0-100 (default: 70)
        
    Returns:
        List of matching groups with IDs, names, and match scores
    """

@mcp.tool()
async def resolve_category(query: str, threshold: int = 70) -> list:
    """
    Resolve a natural language category reference to category ID(s).
    
    Args:
        query: Category name (e.g., "food", "groceries", "utilities")
        threshold: Minimum match score 0-100 (default: 70)
        
    Returns:
        List of matching categories with IDs, names, and match scores
    """
```

#### Comment Tools

```python
@mcp.tool()
async def create_comment(expense_id: int, content: str) -> dict:
    """Create a comment on an expense."""

@mcp.tool()
async def get_comments(expense_id: int) -> dict:
    """Get all comments for an expense."""

@mcp.tool()
async def delete_comment(comment_id: int) -> dict:
    """Delete a comment."""
```

#### Utility Tools

```python
@mcp.tool()
async def get_categories() -> dict:
    """Get all supported expense categories and subcategories."""

@mcp.tool()
async def get_currencies() -> dict:
    """Get all supported currency codes."""
```

## Data Models

### Configuration Model

```python
@dataclass
class SplitwiseConfig:
    """Configuration for Splitwise MCP Server."""
    
    # Authentication (one of these must be provided)
    oauth_consumer_key: Optional[str] = None
    oauth_consumer_secret: Optional[str] = None
    oauth_access_token: Optional[str] = None
    api_key: Optional[str] = None
    
    # Cache settings
    cache_ttl_seconds: int = 86400  # 24 hours
    
    # Resolution settings
    default_match_threshold: int = 70
    
    @classmethod
    def from_env(cls) -> "SplitwiseConfig":
        """Load configuration from environment variables."""
```

### Response Models

```python
@dataclass
class ExpenseUser:
    """User split information for an expense."""
    user_id: int
    paid_share: str  # Decimal as string
    owed_share: str  # Decimal as string
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None

@dataclass
class ResolutionMatch:
    """Result from entity resolution."""
    id: int
    name: str
    match_score: float  # 0-100
    additional_info: dict  # Extra context (email, balance, etc.)
```

## Error Handling

### Error Categories

1. **Authentication Errors** (401)
   - Invalid or expired OAuth token
   - Invalid API key
   - Missing authentication credentials

2. **Authorization Errors** (403)
   - Insufficient permissions
   - Attempting to access another user's private data

3. **Not Found Errors** (404)
   - Invalid expense/group/user ID
   - Deleted or non-existent resource

4. **Validation Errors** (400)
   - Invalid parameter format
   - Missing required fields
   - Invalid currency or category ID

5. **Rate Limit Errors** (429)
   - Too many requests in time window

6. **Server Errors** (500+)
   - Splitwise API issues
   - Network connectivity problems

### Error Response Format

```python
@dataclass
class MCPError:
    """Standardized error response."""
    error_type: str  # "authentication", "validation", "not_found", etc.
    message: str
    status_code: int
    details: Optional[dict] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for MCP response."""
```

### Error Handling Strategy

```python
async def handle_api_error(response: httpx.Response) -> MCPError:
    """Convert HTTP errors to structured MCP errors."""
    
    error_map = {
        401: ("authentication", "Authentication failed. Check your credentials."),
        403: ("authorization", "Access forbidden. Insufficient permissions."),
        404: ("not_found", "Resource not found."),
        400: ("validation", "Invalid request parameters."),
        429: ("rate_limit", "Rate limit exceeded. Please try again later."),
        500: ("server_error", "Splitwise API error. Please try again."),
    }
    
    error_type, default_message = error_map.get(
        response.status_code,
        ("unknown", "An unexpected error occurred.")
    )
    
    try:
        error_data = response.json()
        message = error_data.get("error", default_message)
        details = error_data.get("errors", {})
    except:
        message = default_message
        details = {}
    
    return MCPError(
        error_type=error_type,
        message=message,
        status_code=response.status_code,
        details=details
    )
```

## Testing Strategy

### Unit Tests

1. **Authentication Tests**
   - OAuth token generation and validation
   - API key header generation
   - Token expiration handling

2. **Client Tests**
   - HTTP request/response handling
   - Error parsing and conversion
   - Endpoint URL construction

3. **Resolution Tests**
   - Fuzzy matching accuracy
   - Threshold filtering
   - Multiple match handling
   - Edge cases (empty lists, special characters)

4. **Cache Tests**
   - TTL expiration
   - Cache hit/miss scenarios
   - Cache invalidation

### Integration Tests

1. **End-to-End Expense Flow**
   - Create expense → Get expense → Update expense → Delete expense

2. **Group Management Flow**
   - Create group → Add users → Create expense in group → Remove users → Delete group

3. **Friend Management Flow**
   - Get friends → Resolve friend by name → Create expense with friend → Get friend details

4. **Resolution Flow**
   - Resolve friend by partial name → Create expense using resolved ID

### Test Data

- Use Splitwise sandbox/test environment if available
- Mock API responses for unit tests
- Create test fixtures for common scenarios
- Use pytest with async support (pytest-asyncio)

### Testing Tools

- **pytest**: Test framework
- **pytest-asyncio**: Async test support
- **httpx-mock**: HTTP request mocking
- **pytest-cov**: Code coverage reporting

## Security Considerations

### Authentication Security

1. **Credential Storage**
   - Store OAuth tokens and API keys in environment variables
   - Never commit credentials to version control
   - Use `.env` files with `.gitignore` entry

2. **Token Management**
   - Implement secure token storage
   - Provide token refresh guidance
   - Clear tokens on logout/reset

### API Security

1. **HTTPS Only**
   - All API requests use HTTPS
   - Verify SSL certificates

2. **Input Validation**
   - Validate all user inputs before API calls
   - Sanitize strings to prevent injection
   - Validate numeric ranges and formats

3. **Rate Limiting**
   - Implement client-side rate limiting
   - Handle 429 responses gracefully
   - Provide backoff strategies

### Data Privacy

1. **Minimal Data Exposure**
   - Only return requested data
   - Filter sensitive information
   - Log without exposing credentials

2. **User Consent**
   - OAuth flow requires explicit user consent
   - Clear documentation of data access

## Deployment and Configuration

### Installation

```bash
# Install via pip (when published)
pip install splitwise-mcp-server

# Or install from source
git clone https://github.com/yourusername/splitwise-mcp-server
cd splitwise-mcp-server
pip install -e .
```

### Configuration

#### Environment Variables

```bash
# OAuth Authentication (recommended)
SPLITWISE_OAUTH_CONSUMER_KEY=your_consumer_key
SPLITWISE_OAUTH_CONSUMER_SECRET=your_consumer_secret
SPLITWISE_OAUTH_ACCESS_TOKEN=your_access_token

# OR API Key Authentication
SPLITWISE_API_KEY=your_api_key

# Optional settings
SPLITWISE_CACHE_TTL=86400
SPLITWISE_MATCH_THRESHOLD=70
```

#### MCP Configuration

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

### OAuth Setup Process

1. **Register Application**
   - Go to https://secure.splitwise.com/apps
   - Create new application
   - Note consumer key and secret

2. **Get Access Token**
   - Run OAuth helper script
   - Authorize application in browser
   - Copy access token to environment

3. **Configure MCP Server**
   - Add token to environment variables
   - Test connection with get-current-user tool

## Performance Considerations

### Caching Strategy

- Cache categories and currencies for 24 hours
- Cache friends and groups for 5 minutes (configurable)
- Invalidate cache on write operations

### Connection Pooling

- Use httpx with connection pooling
- Reuse HTTP connections for multiple requests
- Configure reasonable timeout values

### Async Operations

- All API calls are async
- Support concurrent tool invocations
- Use asyncio for parallel requests when appropriate

## Future Enhancements

1. **Advanced Resolution**
   - Context-aware resolution (recent expenses, frequent contacts)
   - Learning from user corrections
   - Multi-entity resolution in single query

2. **Batch Operations**
   - Create multiple expenses at once
   - Bulk friend additions
   - Batch updates

3. **Notifications**
   - Subscribe to expense updates
   - Real-time balance changes
   - Comment notifications

4. **Analytics**
   - Spending summaries
   - Category breakdowns
   - Group balance reports

5. **Receipt Management**
   - Upload receipt images
   - OCR for expense extraction
   - Receipt storage and retrieval
