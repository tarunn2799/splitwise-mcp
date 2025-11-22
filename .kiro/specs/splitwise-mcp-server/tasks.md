# Implementation Plan

- [x] 1. Set up project structure and dependencies
  - Create Python package structure with proper module organization
  - Set up pyproject.toml with FastMCP, httpx, rapidfuzz, python-dotenv dependencies
  - Create .env.example file with required environment variables
  - Set up .gitignore to exclude credentials and cache files
  - _Requirements: 10.1, 10.2_

- [x] 2. Implement authentication layer
  - [x] 2.1 Create OAuth2Handler class for OAuth 2.0 authentication
    - Implement initialization with consumer key and secret
    - Implement access token retrieval from environment
    - Implement authentication header generation for API requests
    - _Requirements: 1.1, 1.3_
  
  - [x] 2.2 Create APIKeyHandler class for API key authentication
    - Implement initialization with API key
    - Implement authentication header generation
    - _Requirements: 1.2, 1.3_
  
  - [x] 2.3 Create configuration loader
    - Implement SplitwiseConfig dataclass with from_env() method
    - Load authentication credentials from environment variables
    - Validate that at least one authentication method is configured
    - _Requirements: 1.3, 1.4_

- [x] 3. Implement core SplitwiseClient service
  - [x] 3.1 Create base HTTP client with error handling
    - Initialize httpx AsyncClient with connection pooling
    - Implement generic get(), post(), put(), delete() methods
    - Implement handle_api_error() for structured error responses
    - Add request/response logging (without exposing credentials)
    - _Requirements: 9.1, 9.4_
  
  - [x] 3.2 Implement user endpoints
    - Implement get_current_user() method
    - Implement get_user(user_id) method
    - _Requirements: 2.1, 2.2, 2.3_
  
  - [x] 3.3 Implement expense endpoints
    - Implement get_expenses() with filtering parameters
    - Implement get_expense(expense_id) method
    - Implement create_expense() method with user splits
    - Implement update_expense() method
    - Implement delete_expense() method
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_
  
  - [x] 3.4 Implement group endpoints
    - Implement get_groups() method
    - Implement get_group(group_id) method
    - Implement create_group() method
    - Implement delete_group() method
    - Implement add_user_to_group() method
    - Implement remove_user_from_group() method
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7_
  
  - [x] 3.5 Implement friend endpoints
    - Implement get_friends() method
    - Implement get_friend(user_id) method
    - _Requirements: 5.1, 5.2, 5.3_
  
  - [x] 3.6 Implement comment endpoints
    - Implement get_comments(expense_id) method
    - Implement create_comment() method
    - Implement delete_comment() method
    - _Requirements: 8.1, 8.2, 8.3, 8.4_
  
  - [x] 3.7 Implement utility endpoints
    - Implement get_categories() method
    - Implement get_currencies() method
    - _Requirements: 7.1, 7.2_

- [x] 4. Implement caching layer
  - Create CacheManager class with TTL support
  - Implement get(), set(), and clear() methods
  - Add timestamp tracking for cache expiration
  - Integrate caching for categories and currencies
  - _Requirements: 7.3, 7.4_

- [x] 5. Implement entity resolution service
  - [x] 5.1 Create EntityResolver class
    - Initialize with SplitwiseClient instance
    - Implement _fuzzy_match() helper using rapidfuzz
    - _Requirements: 6.1, 6.2, 6.5_
  
  - [x] 5.2 Implement friend resolution
    - Implement resolve_friend() method with fuzzy matching
    - Fetch friends list and cache results
    - Return matches with scores above threshold
    - _Requirements: 6.1, 6.3, 6.4, 6.5_
  
  - [x] 5.3 Implement group resolution
    - Implement resolve_group() method with fuzzy matching
    - Fetch groups list and cache results
    - Return matches with scores above threshold
    - _Requirements: 6.2, 6.3, 6.4, 6.5_
  
  - [x] 5.4 Implement category resolution
    - Implement resolve_category() method with fuzzy matching
    - Use cached categories from CacheManager
    - Return matches with scores above threshold
    - _Requirements: 6.3, 6.4, 6.5_

- [ ] 6. Implement MCP tool layer with FastMCP
  - [x] 6.1 Create FastMCP server initialization
    - Initialize FastMCP application
    - Set up SplitwiseClient and EntityResolver instances
    - Configure error handling middleware
    - _Requirements: 10.1_
  
  - [x] 6.2 Implement user tools
    - Create @mcp.tool() for get_current_user
    - Create @mcp.tool() for get_user
    - Add comprehensive docstrings with parameter descriptions
    - _Requirements: 2.1, 2.2, 10.4_
  
  - [x] 6.3 Implement expense tools
    - Create @mcp.tool() for create_expense with all parameters
    - Create @mcp.tool() for get_expenses with filtering
    - Create @mcp.tool() for get_expense
    - Create @mcp.tool() for update_expense
    - Create @mcp.tool() for delete_expense
    - Add input validation for required parameters
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 9.2, 10.4_
  
  - [x] 6.4 Implement group tools
    - Create @mcp.tool() for get_groups
    - Create @mcp.tool() for get_group
    - Create @mcp.tool() for create_group
    - Create @mcp.tool() for delete_group
    - Create @mcp.tool() for add_user_to_group
    - Create @mcp.tool() for remove_user_from_group
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 10.4_
  
  - [x] 6.5 Implement friend tools
    - Create @mcp.tool() for get_friends
    - Create @mcp.tool() for get_friend
    - _Requirements: 5.1, 5.2, 10.4_
  
  - [x] 6.6 Implement resolution tools
    - Create @mcp.tool() for resolve_friend
    - Create @mcp.tool() for resolve_group
    - Create @mcp.tool() for resolve_category
    - Add threshold parameter with default value
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 10.4_
  
  - [x] 6.7 Implement comment tools
    - Create @mcp.tool() for create_comment
    - Create @mcp.tool() for get_comments
    - Create @mcp.tool() for delete_comment
    - _Requirements: 8.1, 8.2, 8.3, 10.4_
  
  - [x] 6.8 Implement utility tools
    - Create @mcp.tool() for get_categories
    - Create @mcp.tool() for get_currencies
    - _Requirements: 7.1, 7.2, 10.4_

- [x] 7. Implement error handling and validation
  - Create MCPError dataclass for structured error responses
  - Implement validation for required parameters in all tools
  - Add specific error messages for common failure scenarios
  - Implement rate limit detection and retry guidance
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [x] 8. Create documentation
  - [x] 8.1 Write comprehensive README.md
    - Add project overview and features section
    - Write installation instructions
    - Document OAuth setup process with step-by-step guide
    - Add MCP configuration examples
    - Include usage examples for common operations
    - Add troubleshooting section for common errors
    - _Requirements: 10.1, 10.2, 10.3, 10.5_
  
  - [x] 8.2 Create OAuth setup helper script
    - Write script to guide users through OAuth flow
    - Generate authorization URL
    - Prompt for authorization code
    - Exchange code for access token
    - Save token to .env file
    - _Requirements: 1.1, 10.3_
  
  - [x] 8.3 Document all MCP tools
    - Create TOOLS.md with complete tool reference
    - Document all parameters with types and constraints
    - Add example requests and responses for each tool
    - Include error codes and meanings
    - _Requirements: 10.4_

- [ ] 9. Create example usage scripts
  - Write example script for creating an expense
  - Write example script for resolving friends and creating group expense
  - Write example script for getting expense history with filters
  - Write example script for managing groups
  - _Requirements: 10.2_

- [x] 10. Set up package distribution
  - Configure pyproject.toml for package publishing
  - Create setup.py if needed for compatibility
  - Add package metadata (version, author, license, description)
  - Create MANIFEST.in for including non-Python files
  - Test package installation in clean environment
  - _Requirements: 10.1_
