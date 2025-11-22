"""FastMCP server implementation with tool definitions."""

import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional, List, Dict, Any, AsyncIterator
from fastmcp import FastMCP

from .config import SplitwiseConfig
from .auth import OAuth2Handler, APIKeyHandler
from .client import SplitwiseClient
from .resolver import EntityResolver
from .errors import (
    ValidationError,
    RateLimitError,
    validate_required,
    validate_positive_number,
    validate_currency_code,
    validate_date_format,
    validate_email,
    validate_range,
    validate_choice,
    validate_user_split
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global instances (initialized in lifespan)
client: Optional[SplitwiseClient] = None
resolver: Optional[EntityResolver] = None


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[None]:
    """Lifespan context manager for server startup and shutdown.
    
    This function handles initialization and cleanup of resources that should
    persist for the lifetime of the server, not per-session.
    
    Args:
        server: The FastMCP server instance
        
    Yields:
        None
    """
    global client, resolver
    
    # Startup: Initialize resources
    logger.info("Starting Splitwise MCP Server...")
    
    # Load configuration from environment
    config = SplitwiseConfig.from_env()
    
    # Set up logging level
    logging.getLogger().setLevel(config.log_level)
    
    # Initialize authentication handler
    if config.has_oauth():
        logger.info("Using OAuth2 authentication")
        auth_handler = OAuth2Handler(
            consumer_key=config.oauth_consumer_key,
            consumer_secret=config.oauth_consumer_secret,
            access_token=config.oauth_access_token
        )
    elif config.has_api_key():
        logger.info("Using API Key authentication")
        auth_handler = APIKeyHandler(api_key=config.api_key)
    else:
        raise ValueError("No valid authentication method configured")
    
    # Initialize SplitwiseClient
    client = SplitwiseClient(auth_handler, cache_ttl=config.cache_ttl_seconds)
    logger.info("SplitwiseClient initialized")
    
    # Initialize EntityResolver
    resolver = EntityResolver(client)
    logger.info("EntityResolver initialized")
    
    logger.info("Splitwise MCP Server started successfully")
    
    try:
        yield
    finally:
        # Shutdown: Cleanup resources
        logger.info("Shutting down Splitwise MCP Server...")
        if client:
            await client.close()
            logger.info("SplitwiseClient closed")
        logger.info("Splitwise MCP Server shutdown complete")


def create_server() -> FastMCP:
    """Create and configure the FastMCP server instance.
    
    This function creates the FastMCP server with all Splitwise tools and
    configures the lifespan for proper resource management.
    
    Returns:
        Configured FastMCP server instance
        
    Raises:
        ValueError: If authentication configuration is invalid
    """
    # Create FastMCP server with lifespan
    mcp = FastMCP("Splitwise MCP Server", lifespan=lifespan)
    logger.info("FastMCP server created")
    
    # Register all tools
    register_user_tools(mcp)
    register_expense_tools(mcp)
    register_group_tools(mcp)
    register_friend_tools(mcp)
    register_resolution_tools(mcp)
    register_comment_tools(mcp)
    register_utility_tools(mcp)
    register_arithmetic_tools(mcp)
    
    logger.info("All tools registered successfully")
    
    return mcp



# ============================================================================
# User Tools
# ============================================================================

def register_user_tools(mcp: FastMCP) -> None:
    """Register user-related MCP tools."""
    
    @mcp.tool()
    async def get_current_user() -> Dict[str, Any]:
        """Get information about the currently authenticated user.
        
        Returns detailed profile information for the authenticated user including
        their ID, name, email, registration status, and profile picture.
        
        Returns:
            Dictionary containing user profile information:
            - id: User ID
            - first_name: User's first name
            - last_name: User's last name
            - email: User's email address
            - registration_status: Registration status
            - picture: Profile picture information
            
        Raises:
            Exception: If authentication fails or API request fails
        """
        try:
            result = await client.get_current_user()
            logger.info("Retrieved current user information")
            return result
        except Exception as e:
            logger.error(f"Error getting current user: {e}")
            raise
    
    @mcp.tool()
    async def get_user(user_id: int) -> Dict[str, Any]:
        """Get information about a specific user by ID.
        
        Retrieves detailed information about any Splitwise user by their user ID.
        This can be used to get information about friends or group members.
        
        Args:
            user_id: The ID of the user to retrieve
            
        Returns:
            Dictionary containing user information:
            - id: User ID
            - first_name: User's first name
            - last_name: User's last name
            - email: User's email address
            - picture: Profile picture information
            
        Raises:
            Exception: If user not found or API request fails
        """
        try:
            result = await client.get_user(user_id)
            logger.info(f"Retrieved user information for user_id={user_id}")
            return result
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            raise


# ============================================================================
# Expense Tools
# ============================================================================

def register_expense_tools(mcp: FastMCP) -> None:
    """Register expense-related MCP tools."""
    
    @mcp.tool()
    async def create_expense(
        cost: str,
        description: str,
        group_id: int = 0,
        currency_code: str = "USD",
        date: Optional[str] = None,
        category_id: Optional[int] = None,
        users: Optional[List[Dict[str, Any]]] = None,
        split_equally: bool = True
    ) -> Dict[str, Any]:
        """Create a new expense in Splitwise.
        
        Creates a new expense with the specified details. The expense can be split
        equally among users or with custom split amounts. If no date is provided,
        the current date/time is used.
        
        IMPORTANT: For any calculations involving amounts, you MUST use the arithmetic
        tools (add, subtract, multiply, divide, modulo) BEFORE calling this tool.
        These tools ensure accurate calculations with proper rounding and handle
        multiple inputs efficiently. Examples:
        - Adding line items: add([12.50, 8.75, 15.00])
        - Applying tax: multiply([100, 1.08])
        - Splitting bills: divide([120, 4])
        - Calculating tips: multiply([85, 1.18]) then divide by people
        
        Args:
            cost: Total amount as string with 2 decimal places (e.g., "25.50")
            description: Short description of the expense
            group_id: Group ID for group expenses (default: 0 for non-group expense)
            currency_code: Three-letter currency code (default: "USD")
            date: ISO 8601 datetime string (default: current date/time)
            category_id: Category ID from get_categories (optional)
            users: List of user split information with user_id, paid_share, owed_share (optional)
            split_equally: Whether to split the expense equally among users (default: True)
            
        Returns:
            Dictionary containing created expense information including:
            - id: Expense ID
            - description: Expense description
            - cost: Total cost
            - date: Expense date
            - users: List of users involved in the split
            
        Raises:
            ValidationError: If input validation fails
            RateLimitError: If rate limit is exceeded
            Exception: If API request fails
        """
        try:
            # Validate required parameters
            validate_required(cost, "cost")
            validate_required(description, "description")
            
            # Validate cost is a positive number
            validate_positive_number(cost, "cost")
            
            # Validate currency code format
            validate_currency_code(currency_code)
            
            # Validate date format if provided
            if date:
                validate_date_format(date, "date")
            
            # Validate group_id is non-negative
            if group_id < 0:
                raise ValidationError(
                    "group_id must be non-negative (use 0 for non-group expenses)",
                    field="group_id",
                    details={"value": group_id}
                )
            
            # Validate category_id is positive if provided
            if category_id is not None and category_id <= 0:
                raise ValidationError(
                    "category_id must be a positive integer",
                    field="category_id",
                    details={"value": category_id}
                )
            
            # Validate users list if provided
            if users:
                validate_user_split(users)
            
            # Build expense data
            expense_data = {
                "cost": cost,
                "description": description,
                "currency_code": currency_code,
                "group_id": group_id,
                "split_equally": split_equally
            }
            
            # Add optional parameters
            if date:
                expense_data["date"] = date
            else:
                expense_data["date"] = datetime.utcnow().isoformat() + "Z"
            
            if category_id is not None:
                expense_data["category_id"] = category_id
            
            if users:
                expense_data["users"] = users
            
            result = await client.create_expense(expense_data)
            logger.info(f"Created expense: {description} (${cost})")
            return result
        except (ValidationError, RateLimitError):
            # Re-raise validation and rate limit errors without wrapping
            raise
        except Exception as e:
            logger.error(f"Error creating expense: {e}")
            raise
    
    @mcp.tool()
    async def get_expenses(
        group_id: Optional[int] = None,
        friend_id: Optional[int] = None,
        dated_after: Optional[str] = None,
        dated_before: Optional[str] = None,
        updated_after: Optional[str] = None,
        updated_before: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Get list of expenses with optional filters.
        
        Retrieves a list of expenses with various filtering options. Results are
        paginated using limit and offset parameters.
        
        Args:
            group_id: Filter by group ID (optional)
            friend_id: Filter by friend user ID (optional)
            dated_after: Filter expenses dated after this date in ISO 8601 format (optional)
            dated_before: Filter expenses dated before this date in ISO 8601 format (optional)
            updated_after: Filter expenses updated after this date in ISO 8601 format (optional)
            updated_before: Filter expenses updated before this date in ISO 8601 format (optional)
            limit: Maximum number of expenses to return (default: 20, max: 100)
            offset: Number of expenses to skip for pagination (default: 0)
            
        Returns:
            Dictionary containing:
            - expenses: List of expense objects
            - Each expense includes id, description, cost, date, users, etc.
            
        Raises:
            ValidationError: If input validation fails
            RateLimitError: If rate limit is exceeded
            Exception: If API request fails
        """
        try:
            # Validate date formats if provided
            if dated_after:
                validate_date_format(dated_after, "dated_after")
            if dated_before:
                validate_date_format(dated_before, "dated_before")
            if updated_after:
                validate_date_format(updated_after, "updated_after")
            if updated_before:
                validate_date_format(updated_before, "updated_before")
            
            # Validate pagination parameters
            validate_range(limit, "limit", min_val=1, max_val=100)
            validate_range(offset, "offset", min_val=0)
            
            result = await client.get_expenses(
                group_id=group_id,
                friend_id=friend_id,
                dated_after=dated_after,
                dated_before=dated_before,
                updated_after=updated_after,
                updated_before=updated_before,
                limit=limit,
                offset=offset
            )
            logger.info(f"Retrieved expenses (limit={limit}, offset={offset})")
            return result
        except (ValidationError, RateLimitError):
            raise
        except Exception as e:
            logger.error(f"Error getting expenses: {e}")
            raise
    
    @mcp.tool()
    async def get_expense(expense_id: int) -> Dict[str, Any]:
        """Get detailed information about a specific expense.
        
        Retrieves complete details for a single expense including all users
        involved in the split, payment information, and comments.
        
        Args:
            expense_id: The ID of the expense to retrieve
            
        Returns:
            Dictionary containing expense details:
            - id: Expense ID
            - description: Expense description
            - cost: Total cost
            - currency_code: Currency code
            - date: Expense date
            - category: Category information
            - users: List of users with paid_share and owed_share
            - comments: List of comments on the expense
            
        Raises:
            Exception: If expense not found or API request fails
        """
        try:
            result = await client.get_expense(expense_id)
            logger.info(f"Retrieved expense {expense_id}")
            return result
        except Exception as e:
            logger.error(f"Error getting expense {expense_id}: {e}")
            raise
    
    @mcp.tool()
    async def update_expense(
        expense_id: int,
        cost: Optional[str] = None,
        description: Optional[str] = None,
        date: Optional[str] = None,
        category_id: Optional[int] = None,
        users: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Update an existing expense.
        
        Updates one or more fields of an existing expense. Only provided fields
        will be updated; other fields remain unchanged.
        
        Args:
            expense_id: The ID of the expense to update
            cost: New total amount as string (optional)
            description: New description (optional)
            date: New date in ISO 8601 format (optional)
            category_id: New category ID (optional)
            users: Updated user split information (optional)
            
        Returns:
            Dictionary containing updated expense information
            
        Raises:
            ValidationError: If input validation fails
            RateLimitError: If rate limit is exceeded
            Exception: If expense not found or API request fails
        """
        try:
            # Validate expense_id
            validate_required(expense_id, "expense_id")
            if expense_id <= 0:
                raise ValidationError(
                    "expense_id must be a positive integer",
                    field="expense_id",
                    details={"value": expense_id}
                )
            
            # Validate cost if provided
            if cost is not None:
                validate_positive_number(cost, "cost")
            
            # Validate date format if provided
            if date is not None:
                validate_date_format(date, "date")
            
            # Validate category_id if provided
            if category_id is not None and category_id <= 0:
                raise ValidationError(
                    "category_id must be a positive integer",
                    field="category_id",
                    details={"value": category_id}
                )
            
            # Validate users list if provided
            if users is not None:
                validate_user_split(users)
            
            # Build update data with only provided fields
            expense_data = {}
            if cost is not None:
                expense_data["cost"] = cost
            if description is not None:
                expense_data["description"] = description
            if date is not None:
                expense_data["date"] = date
            if category_id is not None:
                expense_data["category_id"] = category_id
            if users is not None:
                expense_data["users"] = users
            
            if not expense_data:
                raise ValidationError(
                    "At least one field must be provided to update",
                    details={"provided_fields": []}
                )
            
            result = await client.update_expense(expense_id, expense_data)
            logger.info(f"Updated expense {expense_id}")
            return result
        except (ValidationError, RateLimitError):
            raise
        except Exception as e:
            logger.error(f"Error updating expense {expense_id}: {e}")
            raise
    
    @mcp.tool()
    async def delete_expense(expense_id: int) -> Dict[str, Any]:
        """Delete an expense.
        
        Permanently deletes an expense from Splitwise. This action cannot be undone.
        
        Args:
            expense_id: The ID of the expense to delete
            
        Returns:
            Dictionary with success status
            
        Raises:
            Exception: If expense not found or API request fails
        """
        try:
            result = await client.delete_expense(expense_id)
            logger.info(f"Deleted expense {expense_id}")
            return result
        except Exception as e:
            logger.error(f"Error deleting expense {expense_id}: {e}")
            raise


# ============================================================================
# Group Tools
# ============================================================================

def register_group_tools(mcp: FastMCP) -> None:
    """Register group-related MCP tools."""
    
    @mcp.tool()
    async def get_groups() -> Dict[str, Any]:
        """Get all groups for the current user.
        
        Retrieves a list of all groups that the authenticated user is a member of,
        including group details and member information.
        
        Returns:
            Dictionary containing:
            - groups: List of group objects
            - Each group includes id, name, members, simplify_by_default, etc.
            
        Raises:
            Exception: If API request fails
        """
        try:
            result = await client.get_groups()
            logger.info("Retrieved groups list")
            return result
        except Exception as e:
            logger.error(f"Error getting groups: {e}")
            raise
    
    @mcp.tool()
    async def get_group(group_id: int) -> Dict[str, Any]:
        """Get detailed information about a specific group.
        
        Retrieves complete details for a single group including all members,
        balances, and debt information.
        
        Args:
            group_id: The ID of the group to retrieve
            
        Returns:
            Dictionary containing group details:
            - id: Group ID
            - name: Group name
            - members: List of members with balance information
            - simplify_by_default: Whether debt simplification is enabled
            - original_debts: List of debts before simplification
            - simplified_debts: List of simplified debts
            
        Raises:
            Exception: If group not found or API request fails
        """
        try:
            result = await client.get_group(group_id)
            logger.info(f"Retrieved group {group_id}")
            return result
        except Exception as e:
            logger.error(f"Error getting group {group_id}: {e}")
            raise
    
    @mcp.tool()
    async def create_group(
        name: str,
        group_type: str = "other",
        simplify_by_default: bool = True,
        users: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Create a new group.
        
        Creates a new group with the specified name and settings. You can optionally
        add initial members when creating the group.
        
        Args:
            name: Group name (required)
            group_type: Type of group - "home", "trip", "couple", or "other" (default: "other")
            simplify_by_default: Enable debt simplification (default: True)
            users: List of initial members with user_id, first_name, last_name, email (optional)
            
        Returns:
            Dictionary containing created group information:
            - id: Group ID
            - name: Group name
            - members: List of group members
            
        Raises:
            ValidationError: If input validation fails
            RateLimitError: If rate limit is exceeded
            Exception: If API request fails
        """
        try:
            # Validate required parameters
            validate_required(name, "name")
            
            # Validate group_type
            valid_types = ["home", "trip", "couple", "other"]
            validate_choice(group_type, "group_type", valid_types)
            
            # Validate users list if provided
            if users:
                if not isinstance(users, list):
                    raise ValidationError(
                        "users must be a list",
                        field="users",
                        details={"type": type(users).__name__}
                    )
                
                for i, user in enumerate(users):
                    if not isinstance(user, dict):
                        raise ValidationError(
                            f"users[{i}] must be a dictionary",
                            field="users",
                            details={"index": i, "type": type(user).__name__}
                        )
                    
                    # Validate email if provided
                    if "email" in user and user["email"]:
                        validate_email(user["email"])
            
            group_data = {
                "name": name,
                "group_type": group_type,
                "simplify_by_default": simplify_by_default
            }
            
            if users:
                group_data["users"] = users
            
            result = await client.create_group(group_data)
            logger.info(f"Created group: {name}")
            
            # Clear resolver cache since groups list changed
            resolver.clear_cache()
            
            return result
        except (ValidationError, RateLimitError):
            raise
        except Exception as e:
            logger.error(f"Error creating group: {e}")
            raise
    
    @mcp.tool()
    async def delete_group(group_id: int) -> Dict[str, Any]:
        """Delete a group.
        
        Permanently deletes a group from Splitwise. This action cannot be undone.
        All expenses in the group must be settled before deletion.
        
        Args:
            group_id: The ID of the group to delete
            
        Returns:
            Dictionary with success status
            
        Raises:
            Exception: If group not found, has unsettled expenses, or API request fails
        """
        try:
            result = await client.delete_group(group_id)
            logger.info(f"Deleted group {group_id}")
            
            # Clear resolver cache since groups list changed
            resolver.clear_cache()
            
            return result
        except Exception as e:
            logger.error(f"Error deleting group {group_id}: {e}")
            raise
    
    @mcp.tool()
    async def add_user_to_group(
        group_id: int,
        user_id: Optional[int] = None,
        email: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Add a user to a group.
        
        Adds a user to an existing group. You can specify the user by ID or by
        email and name (for inviting new users to Splitwise).
        
        Args:
            group_id: The ID of the group
            user_id: ID of existing Splitwise user to add (optional if email provided)
            email: Email address of user to add (optional if user_id provided)
            first_name: First name of user (optional, used with email)
            last_name: Last name of user (optional, used with email)
            
        Returns:
            Dictionary with success status and updated group information
            
        Raises:
            ValidationError: If input validation fails
            RateLimitError: If rate limit is exceeded
            Exception: If group or user not found, or API request fails
        """
        try:
            # Validate group_id
            validate_required(group_id, "group_id")
            if group_id <= 0:
                raise ValidationError(
                    "group_id must be a positive integer",
                    field="group_id",
                    details={"value": group_id}
                )
            
            # Validate that either user_id or email is provided
            if not user_id and not email:
                raise ValidationError(
                    "Either user_id or email must be provided",
                    details={"user_id": user_id, "email": email}
                )
            
            # Validate user_id if provided
            if user_id is not None and user_id <= 0:
                raise ValidationError(
                    "user_id must be a positive integer",
                    field="user_id",
                    details={"value": user_id}
                )
            
            # Validate email if provided
            if email:
                validate_email(email)
            
            user_data = {}
            if user_id is not None:
                user_data["user_id"] = user_id
            if email:
                user_data["email"] = email
            if first_name:
                user_data["first_name"] = first_name
            if last_name:
                user_data["last_name"] = last_name
            
            result = await client.add_user_to_group(group_id, user_data)
            logger.info(f"Added user to group {group_id}")
            return result
        except (ValidationError, RateLimitError):
            raise
        except Exception as e:
            logger.error(f"Error adding user to group {group_id}: {e}")
            raise
    
    @mcp.tool()
    async def remove_user_from_group(group_id: int, user_id: int) -> Dict[str, Any]:
        """Remove a user from a group.
        
        Removes a user from a group. The user must have a zero balance in the group
        before they can be removed.
        
        Args:
            group_id: The ID of the group
            user_id: The ID of the user to remove
            
        Returns:
            Dictionary with success status
            
        Raises:
            Exception: If user has non-zero balance, not found, or API request fails
        """
        try:
            result = await client.remove_user_from_group(group_id, user_id)
            logger.info(f"Removed user {user_id} from group {group_id}")
            return result
        except Exception as e:
            logger.error(f"Error removing user {user_id} from group {group_id}: {e}")
            raise


# ============================================================================
# Friend Tools
# ============================================================================

def register_friend_tools(mcp: FastMCP) -> None:
    """Register friend-related MCP tools."""
    
    @mcp.tool()
    async def get_friends() -> Dict[str, Any]:
        """Get all friends for the current user.
        
        Retrieves a list of all friends (users you share expenses with) including
        balance information for each friend.
        
        Returns:
            Dictionary containing:
            - friends: List of friend objects
            - Each friend includes id, first_name, last_name, email, balance, etc.
            
        Raises:
            Exception: If API request fails
        """
        try:
            result = await client.get_friends()
            logger.info("Retrieved friends list")
            return result
        except Exception as e:
            logger.error(f"Error getting friends: {e}")
            raise
    
    @mcp.tool()
    async def get_friend(user_id: int) -> Dict[str, Any]:
        """Get detailed information about a specific friend.
        
        Retrieves complete details for a single friend including balance information
        and shared groups.
        
        Args:
            user_id: The ID of the friend to retrieve
            
        Returns:
            Dictionary containing friend details:
            - id: User ID
            - first_name: Friend's first name
            - last_name: Friend's last name
            - email: Friend's email
            - balance: Balance information in different currencies
            - groups: List of shared groups
            
        Raises:
            Exception: If friend not found or API request fails
        """
        try:
            result = await client.get_friend(user_id)
            logger.info(f"Retrieved friend {user_id}")
            return result
        except Exception as e:
            logger.error(f"Error getting friend {user_id}: {e}")
            raise


# ============================================================================
# Resolution Tools
# ============================================================================

def register_resolution_tools(mcp: FastMCP) -> None:
    """Register entity resolution MCP tools."""
    
    @mcp.tool()
    async def resolve_friend(query: str, threshold: int = 70) -> List[Dict[str, Any]]:
        """Resolve a natural language friend reference to user ID(s).
        
        Uses fuzzy matching to find friends whose names match the provided query.
        This is useful when you know a friend's name but not their exact user ID.
        
        Args:
            query: Friend name or partial name (e.g., "John", "john smith")
            threshold: Minimum match score 0-100 (default: 70). Higher values require closer matches.
            
        Returns:
            List of matching friends, each containing:
            - id: Friend's user ID
            - name: Friend's full name
            - match_score: Fuzzy match score (0-100)
            - additional_info: Dict with email, balance, and other details
            
        Raises:
            ValidationError: If input validation fails
            RateLimitError: If rate limit is exceeded
            Exception: If API request fails
        """
        try:
            # Validate query
            validate_required(query, "query")
            
            # Validate threshold range
            validate_range(threshold, "threshold", min_val=0, max_val=100)
            
            matches = await resolver.resolve_friend(query, threshold)
            result = [
                {
                    "id": match.id,
                    "name": match.name,
                    "match_score": match.match_score,
                    "additional_info": match.additional_info
                }
                for match in matches
            ]
            logger.info(f"Resolved friend '{query}': found {len(result)} matches")
            return result
        except (ValidationError, RateLimitError):
            raise
        except Exception as e:
            logger.error(f"Error resolving friend '{query}': {e}")
            raise
    
    @mcp.tool()
    async def resolve_group(query: str, threshold: int = 70) -> List[Dict[str, Any]]:
        """Resolve a natural language group reference to group ID(s).
        
        Uses fuzzy matching to find groups whose names match the provided query.
        This is useful when you know a group's name but not its exact ID.
        
        Args:
            query: Group name or partial name (e.g., "roommates", "paris trip")
            threshold: Minimum match score 0-100 (default: 70). Higher values require closer matches.
            
        Returns:
            List of matching groups, each containing:
            - id: Group ID
            - name: Group name
            - match_score: Fuzzy match score (0-100)
            - additional_info: Dict with members, type, and other details
            
        Raises:
            ValidationError: If input validation fails
            RateLimitError: If rate limit is exceeded
            Exception: If API request fails
        """
        try:
            # Validate query
            validate_required(query, "query")
            
            # Validate threshold range
            validate_range(threshold, "threshold", min_val=0, max_val=100)
            
            matches = await resolver.resolve_group(query, threshold)
            result = [
                {
                    "id": match.id,
                    "name": match.name,
                    "match_score": match.match_score,
                    "additional_info": match.additional_info
                }
                for match in matches
            ]
            logger.info(f"Resolved group '{query}': found {len(result)} matches")
            return result
        except (ValidationError, RateLimitError):
            raise
        except Exception as e:
            logger.error(f"Error resolving group '{query}': {e}")
            raise
    
    @mcp.tool()
    async def resolve_category(query: str, threshold: int = 70) -> List[Dict[str, Any]]:
        """Resolve a natural language category reference to category ID(s).
        
        Uses fuzzy matching to find expense categories that match the provided query.
        This is useful when you want to categorize an expense but don't know the exact category ID.
        
        Args:
            query: Category name (e.g., "food", "groceries", "utilities")
            threshold: Minimum match score 0-100 (default: 70). Higher values require closer matches.
            
        Returns:
            List of matching categories, each containing:
            - id: Category ID
            - name: Category name (may include parent category for subcategories)
            - match_score: Fuzzy match score (0-100)
            - additional_info: Dict with subcategories and other details
            
        Raises:
            ValidationError: If input validation fails
            RateLimitError: If rate limit is exceeded
            Exception: If API request fails
        """
        try:
            # Validate query
            validate_required(query, "query")
            
            # Validate threshold range
            validate_range(threshold, "threshold", min_val=0, max_val=100)
            
            matches = await resolver.resolve_category(query, threshold)
            result = [
                {
                    "id": match.id,
                    "name": match.name,
                    "match_score": match.match_score,
                    "additional_info": match.additional_info
                }
                for match in matches
            ]
            logger.info(f"Resolved category '{query}': found {len(result)} matches")
            return result
        except (ValidationError, RateLimitError):
            raise
        except Exception as e:
            logger.error(f"Error resolving category '{query}': {e}")
            raise


# ============================================================================
# Comment Tools
# ============================================================================

def register_comment_tools(mcp: FastMCP) -> None:
    """Register comment-related MCP tools."""
    
    @mcp.tool()
    async def create_comment(expense_id: int, content: str) -> Dict[str, Any]:
        """Create a comment on an expense.
        
        Adds a text comment to an existing expense. Comments are visible to all
        users involved in the expense.
        
        Args:
            expense_id: The ID of the expense to comment on
            content: The comment text content
            
        Returns:
            Dictionary containing created comment information:
            - id: Comment ID
            - content: Comment text
            - user: User who created the comment
            - created_at: Timestamp when comment was created
            
        Raises:
            ValidationError: If input validation fails
            RateLimitError: If rate limit is exceeded
            Exception: If expense not found or API request fails
        """
        try:
            # Validate expense_id
            validate_required(expense_id, "expense_id")
            if expense_id <= 0:
                raise ValidationError(
                    "expense_id must be a positive integer",
                    field="expense_id",
                    details={"value": expense_id}
                )
            
            # Validate content
            validate_required(content, "content")
            
            result = await client.create_comment(expense_id, content)
            logger.info(f"Created comment on expense {expense_id}")
            return result
        except (ValidationError, RateLimitError):
            raise
        except Exception as e:
            logger.error(f"Error creating comment on expense {expense_id}: {e}")
            raise
    
    @mcp.tool()
    async def get_comments(expense_id: int) -> Dict[str, Any]:
        """Get all comments for an expense.
        
        Retrieves all comments associated with a specific expense, including
        comment text, author, and timestamps.
        
        Args:
            expense_id: The ID of the expense
            
        Returns:
            Dictionary containing:
            - comments: List of comment objects
            - Each comment includes id, content, user, created_at, etc.
            
        Raises:
            Exception: If expense not found or API request fails
        """
        try:
            result = await client.get_comments(expense_id)
            logger.info(f"Retrieved comments for expense {expense_id}")
            return result
        except Exception as e:
            logger.error(f"Error getting comments for expense {expense_id}: {e}")
            raise
    
    @mcp.tool()
    async def delete_comment(comment_id: int) -> Dict[str, Any]:
        """Delete a comment.
        
        Permanently deletes a comment from an expense. This action cannot be undone.
        You can only delete your own comments.
        
        Args:
            comment_id: The ID of the comment to delete
            
        Returns:
            Dictionary with success status
            
        Raises:
            Exception: If comment not found, unauthorized, or API request fails
        """
        try:
            result = await client.delete_comment(comment_id)
            logger.info(f"Deleted comment {comment_id}")
            return result
        except Exception as e:
            logger.error(f"Error deleting comment {comment_id}: {e}")
            raise


# ============================================================================
# Utility Tools
# ============================================================================

def register_utility_tools(mcp: FastMCP) -> None:
    """Register utility MCP tools."""
    
    @mcp.tool()
    async def get_categories() -> Dict[str, Any]:
        """Get all supported expense categories and subcategories.
        
        Retrieves the complete list of expense categories available in Splitwise.
        This data is cached to minimize API calls.
        
        Returns:
            Dictionary containing:
            - categories: List of category objects
            - Each category includes id, name, and optional subcategories
            
        Raises:
            Exception: If API request fails
        """
        try:
            result = await client.get_categories()
            logger.info("Retrieved categories")
            return result
        except Exception as e:
            logger.error(f"Error getting categories: {e}")
            raise
    
    @mcp.tool()
    async def get_currencies() -> Dict[str, Any]:
        """Get all supported currency codes.
        
        Retrieves the complete list of currencies supported by Splitwise.
        This data is cached to minimize API calls.
        
        Returns:
            Dictionary containing:
            - currencies: List of currency objects
            - Each currency includes currency_code (e.g., "USD") and unit (e.g., "$")
            
        Raises:
            Exception: If API request fails
        """
        try:
            result = await client.get_currencies()
            logger.info("Retrieved currencies")
            return result
        except Exception as e:
            logger.error(f"Error getting currencies: {e}")
            raise



# ============================================================================


# ============================================================================
# Arithmetic Tools
# ============================================================================

def register_arithmetic_tools(mcp: FastMCP) -> None:
    """Register basic arithmetic calculation tools for expense management."""
    
    @mcp.tool()
    def add(numbers: List[float], decimal_places: int = 2) -> Dict[str, Any]:
        """Add multiple numbers together.
        
        Performs addition on a list of numbers with proper decimal rounding.
        Useful for calculating totals, summing line items, or adding tax/tip to bills.
        
        Examples:
            - Add line items: add([12.50, 8.75, 15.00]) = 36.25
            - Add bill + tax + tip: add([85.00, 7.65, 15.30]) = 107.95
        
        Args:
            numbers: List of numbers to add (minimum 1 number)
            decimal_places: Number of decimal places to round to (default: 2)
            
        Returns:
            Dictionary containing:
            - result: Sum of all numbers
            - result_formatted: Formatted string with specified decimal places
            - operands: Original list of numbers
            - operation: "addition"
            
        Raises:
            ValueError: If numbers list is empty
        """
        if not numbers:
            raise ValueError("numbers list cannot be empty")
        
        result = round(sum(numbers), decimal_places)
        logger.info(f"Addition: {' + '.join(map(str, numbers))} = {result}")
        
        return {
            "result": result,
            "result_formatted": f"{result:.{decimal_places}f}",
            "operands": numbers,
            "operation": "addition"
        }
    
    @mcp.tool()
    def subtract(numbers: List[float], decimal_places: int = 2) -> Dict[str, Any]:
        """Subtract numbers sequentially from left to right.
        
        Performs subtraction on a list of numbers: first - second - third - ...
        Useful for calculating remainders, discounts, or adjustments.
        
        Examples:
            - Calculate change: subtract([100.00, 87.50]) = 12.50
            - Apply discount: subtract([50.00, 5.00]) = 45.00
            - Multiple deductions: subtract([100.00, 10.00, 5.00, 2.50]) = 82.50
        
        Args:
            numbers: List of numbers to subtract (minimum 2 numbers)
            decimal_places: Number of decimal places to round to (default: 2)
            
        Returns:
            Dictionary containing:
            - result: Result of sequential subtraction
            - result_formatted: Formatted string with specified decimal places
            - operands: Original list of numbers
            - operation: "subtraction"
            
        Raises:
            ValueError: If numbers list has fewer than 2 elements
        """
        if len(numbers) < 2:
            raise ValueError("subtract requires at least 2 numbers")
        
        result = numbers[0]
        for num in numbers[1:]:
            result -= num
        result = round(result, decimal_places)
        
        logger.info(f"Subtraction: {' - '.join(map(str, numbers))} = {result}")
        
        return {
            "result": result,
            "result_formatted": f"{result:.{decimal_places}f}",
            "operands": numbers,
            "operation": "subtraction"
        }
    
    @mcp.tool()
    def multiply(numbers: List[float], decimal_places: int = 2) -> Dict[str, Any]:
        """Multiply multiple numbers together.
        
        Performs multiplication on a list of numbers with proper decimal rounding.
        Useful for calculating totals with quantities, applying rates, or scaling amounts.
        
        Examples:
            - Calculate item total: multiply([12.50, 3]) = 37.50 (price × quantity)
            - Apply tax rate: multiply([100.00, 1.08]) = 108.00 (amount × 1.08 for 8% tax)
            - Multiple factors: multiply([10.00, 1.08, 1.15]) = 12.42 (tax + tip)
        
        Args:
            numbers: List of numbers to multiply (minimum 2 numbers)
            decimal_places: Number of decimal places to round to (default: 2)
            
        Returns:
            Dictionary containing:
            - result: Product of all numbers
            - result_formatted: Formatted string with specified decimal places
            - operands: Original list of numbers
            - operation: "multiplication"
            
        Raises:
            ValueError: If numbers list has fewer than 2 elements
        """
        if len(numbers) < 2:
            raise ValueError("multiply requires at least 2 numbers")
        
        result = numbers[0]
        for num in numbers[1:]:
            result *= num
        result = round(result, decimal_places)
        
        logger.info(f"Multiplication: {' × '.join(map(str, numbers))} = {result}")
        
        return {
            "result": result,
            "result_formatted": f"{result:.{decimal_places}f}",
            "operands": numbers,
            "operation": "multiplication"
        }
    
    @mcp.tool()
    def divide(numbers: List[float], decimal_places: int = 2) -> Dict[str, Any]:
        """Divide numbers sequentially from left to right.
        
        Performs division on a list of numbers: first / second / third / ...
        Useful for splitting amounts, calculating per-person costs, or finding rates.
        
        Examples:
            - Split bill: divide([120.00, 4]) = 30.00 (total / people)
            - Calculate unit price: divide([45.00, 3]) = 15.00 (total / quantity)
            - Multiple divisions: divide([100.00, 2, 5]) = 10.00
        
        Args:
            numbers: List of numbers to divide (minimum 2 numbers)
            decimal_places: Number of decimal places to round to (default: 2)
            
        Returns:
            Dictionary containing:
            - result: Result of sequential division
            - result_formatted: Formatted string with specified decimal places
            - operands: Original list of numbers
            - operation: "division"
            
        Raises:
            ValueError: If numbers list has fewer than 2 elements
            ValueError: If any divisor (after the first number) is zero
        """
        if len(numbers) < 2:
            raise ValueError("divide requires at least 2 numbers")
        
        result = numbers[0]
        for i, num in enumerate(numbers[1:], start=1):
            if num == 0:
                raise ValueError(f"Cannot divide by zero (divisor at position {i})")
            result /= num
        result = round(result, decimal_places)
        
        logger.info(f"Division: {' ÷ '.join(map(str, numbers))} = {result}")
        
        return {
            "result": result,
            "result_formatted": f"{result:.{decimal_places}f}",
            "operands": numbers,
            "operation": "division"
        }
    
    @mcp.tool()
    def modulo(a: float, b: float, decimal_places: int = 2) -> Dict[str, Any]:
        """Calculate the remainder of division (modulo operation).
        
        Calculates a % b (the remainder when a is divided by b).
        Useful for checking divisibility or calculating remainders in splits.
        
        Examples:
            - Check remainder: modulo(100.00, 3) = 1.00
            - Verify even split: modulo(120.00, 4) = 0.00 (divides evenly)
        
        Args:
            a: Dividend (number to be divided)
            b: Divisor (number to divide by)
            decimal_places: Number of decimal places to round to (default: 2)
            
        Returns:
            Dictionary containing:
            - result: Remainder of a % b
            - result_formatted: Formatted string with specified decimal places
            - operands: [a, b]
            - operation: "modulo"
            
        Raises:
            ValueError: If b is zero
        """
        if b == 0:
            raise ValueError("Cannot calculate modulo with zero divisor")
        
        result = round(a % b, decimal_places)
        logger.info(f"Modulo: {a} % {b} = {result}")
        
        return {
            "result": result,
            "result_formatted": f"{result:.{decimal_places}f}",
            "operands": [a, b],
            "operation": "modulo"
        }
