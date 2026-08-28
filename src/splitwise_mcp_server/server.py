"""FastMCP server implementation with tool definitions."""

import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
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
    resolver.default_threshold = config.default_match_threshold
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
    register_notification_tools(mcp)
    register_utility_tools(mcp)
    
    logger.info("All tools registered successfully")
    
    return mcp



# ============================================================================
# User Tools
# ============================================================================

def register_user_tools(mcp: FastMCP) -> None:
    """Register user-related MCP tools."""
    
    @mcp.tool()
    async def get_current_user() -> Dict[str, Any]:
        """Get the current authenticated user's profile (id, name, email, picture)."""
        try:
            result = await client.get_current_user()
            logger.info("Retrieved current user information")
            return result
        except Exception as e:
            logger.error(f"Error getting current user: {e}")
            raise
    
    @mcp.tool()
    async def get_user(user_id: int) -> Dict[str, Any]:
        """Get a user's profile by their ID."""
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
        details: Optional[str] = None,
        repeat_interval: Optional[str] = None,
        users: Optional[List[Dict[str, Any]]] = None,
        split_equally: bool = True,
        payment: bool = False,
    ) -> Dict[str, Any]:
        """Create a new expense. Cost is a string with 2 decimals (e.g. "25.50").
        Splits equally by default; provide users list with paid_share/owed_share for custom splits.
        Each user needs user_id or (email + first_name + last_name).
        Set repeat_interval to "weekly", "fortnightly", "monthly", or "yearly" for recurring expenses.
        Set payment=True to create a cash settlement/payment record between users.
        """
        try:
            validate_required(cost, "cost")
            validate_required(description, "description")
            validate_positive_number(cost, "cost")
            validate_currency_code(currency_code)

            if date:
                validate_date_format(date, "date")
            if group_id < 0:
                raise ValidationError(
                    "group_id must be non-negative (use 0 for non-group expenses)",
                    field="group_id",
                    details={"value": group_id}
                )
            if category_id is not None and category_id <= 0:
                raise ValidationError(
                    "category_id must be a positive integer",
                    field="category_id",
                    details={"value": category_id}
                )
            if repeat_interval is not None:
                valid_intervals = ["never", "weekly", "fortnightly", "monthly", "yearly"]
                validate_choice(repeat_interval, "repeat_interval", valid_intervals)
            if users:
                validate_user_split(users)

            expense_data = {
                "cost": cost,
                "description": description,
                "currency_code": currency_code,
                "group_id": group_id,
            }

            if users:
                expense_data["split_equally"] = False
                expense_data["users"] = users
            elif split_equally:
                expense_data["split_equally"] = True

            if date:
                expense_data["date"] = date
            else:
                expense_data["date"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

            if category_id is not None:
                expense_data["category_id"] = category_id
            if details is not None:
                expense_data["details"] = details
            if repeat_interval is not None:
                expense_data["repeat_interval"] = repeat_interval
            if payment:
                expense_data["payment"] = True
                expense_data["creation_method"] = "payment"

            result = await client.create_expense(expense_data)
            logger.info(f"Created expense: {description} (${cost})")
            return result
        except (ValidationError, RateLimitError):
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
        """List expenses with optional filters. Dates are ISO 8601 format. Max limit is 100."""
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
        """Get full details of a single expense including users, splits, and comments."""
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
        currency_code: Optional[str] = None,
        group_id: Optional[int] = None,
        details: Optional[str] = None,
        repeat_interval: Optional[str] = None,
        users: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Update an existing expense. Only provided fields are changed.
        If any users are supplied, all shares for the expense are overwritten with the provided values.
        """
        try:
            validate_required(expense_id, "expense_id")
            if expense_id <= 0:
                raise ValidationError(
                    "expense_id must be a positive integer",
                    field="expense_id",
                    details={"value": expense_id}
                )
            if cost is not None:
                validate_positive_number(cost, "cost")
            if date is not None:
                validate_date_format(date, "date")
            if category_id is not None and category_id <= 0:
                raise ValidationError(
                    "category_id must be a positive integer",
                    field="category_id",
                    details={"value": category_id}
                )
            if currency_code is not None:
                validate_currency_code(currency_code)
            if group_id is not None and group_id < 0:
                raise ValidationError(
                    "group_id must be non-negative",
                    field="group_id",
                    details={"value": group_id}
                )
            if repeat_interval is not None:
                valid_intervals = ["never", "weekly", "fortnightly", "monthly", "yearly"]
                validate_choice(repeat_interval, "repeat_interval", valid_intervals)
            if users is not None:
                validate_user_split(users)

            expense_data = {}
            if cost is not None:
                expense_data["cost"] = cost
            if description is not None:
                expense_data["description"] = description
            if date is not None:
                expense_data["date"] = date
            if category_id is not None:
                expense_data["category_id"] = category_id
            if currency_code is not None:
                expense_data["currency_code"] = currency_code
            if group_id is not None:
                expense_data["group_id"] = group_id
            if details is not None:
                expense_data["details"] = details
            if repeat_interval is not None:
                expense_data["repeat_interval"] = repeat_interval
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
        """Delete an expense permanently. Use restore_expense to undo."""
        try:
            result = await client.delete_expense(expense_id)
            logger.info(f"Deleted expense {expense_id}")
            return result
        except Exception as e:
            logger.error(f"Error deleting expense {expense_id}: {e}")
            raise

    @mcp.tool()
    async def restore_expense(expense_id: int) -> Dict[str, Any]:
        """Restore a previously deleted expense. Use this to undo an accidental deletion."""
        try:
            result = await client.restore_expense(expense_id)
            logger.info(f"Restored expense {expense_id}")
            return result
        except Exception as e:
            logger.error(f"Error restoring expense {expense_id}: {e}")
            raise


# ============================================================================
# Group Tools
# ============================================================================

def register_group_tools(mcp: FastMCP) -> None:
    """Register group-related MCP tools."""
    
    @mcp.tool()
    async def get_groups() -> Dict[str, Any]:
        """List all groups the current user belongs to, with members and balances."""
        try:
            result = await client.get_groups()
            logger.info("Retrieved groups list")
            return result
        except Exception as e:
            logger.error(f"Error getting groups: {e}")
            raise
    
    @mcp.tool()
    async def get_group(group_id: int) -> Dict[str, Any]:
        """Get a group's details including members, balances, and simplified debts."""
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
        """Create a new group. group_type is one of: home, trip, couple, other.
        Optionally add initial members via users list with user_id or email+name."""
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
        """Delete a group. All expenses must be settled first."""
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
        """Add a user to a group by user_id or by email (with first_name/last_name for new invites)."""
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
        """Remove a user from a group. User must have zero balance in the group."""
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
        """List all friends with their balance information."""
        try:
            result = await client.get_friends()
            logger.info("Retrieved friends list")
            return result
        except Exception as e:
            logger.error(f"Error getting friends: {e}")
            raise
    
    @mcp.tool()
    async def get_friend(user_id: int) -> Dict[str, Any]:
        """Get a friend's details including balances and shared groups."""
        try:
            result = await client.get_friend(user_id)
            logger.info(f"Retrieved friend {user_id}")
            return result
        except Exception as e:
            logger.error(f"Error getting friend {user_id}: {e}")
            raise

    @mcp.tool()
    async def create_friend(user_email: str, user_first_name: str = "", user_last_name: str = "") -> Dict[str, Any]:
        """Add a friend by email address. Optionally provide their first and last name."""
        try:
            validate_required(user_email, "user_email")
            validate_email(user_email)
            result = await client.create_friend(user_email, user_first_name, user_last_name)
            resolver.clear_cache()
            logger.info(f"Created friend: {user_email}")
            return result
        except (ValidationError, RateLimitError):
            raise
        except Exception as e:
            logger.error(f"Error creating friend: {e}")
            raise

    @mcp.tool()
    async def delete_friend(friend_id: int) -> Dict[str, Any]:
        """Remove a friendship. Does not affect shared expenses or balances."""
        try:
            result = await client.delete_friend(friend_id)
            resolver.clear_cache()
            logger.info(f"Deleted friend {friend_id}")
            return result
        except Exception as e:
            logger.error(f"Error deleting friend {friend_id}: {e}")
            raise


# ============================================================================
# Resolution Tools
# ============================================================================

def register_resolution_tools(mcp: FastMCP) -> None:
    """Register entity resolution MCP tools."""
    
    @mcp.tool()
    async def resolve_friend(query: str, threshold: Optional[int] = None) -> List[Dict[str, Any]]:
        """Fuzzy-match a friend by name. Returns matches with id, name, and match_score.
        Use this when you know a name but not the user_id."""
        try:
            validate_required(query, "query")
            effective_threshold = threshold if threshold is not None else resolver.default_threshold
            validate_range(effective_threshold, "threshold", min_val=0, max_val=100)

            matches = await resolver.resolve_friend(query, effective_threshold)
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
    async def resolve_group(query: str, threshold: Optional[int] = None) -> List[Dict[str, Any]]:
        """Fuzzy-match a group by name. Returns matches with id, name, and match_score.
        Use this when you know a group name but not the group_id."""
        try:
            validate_required(query, "query")
            effective_threshold = threshold if threshold is not None else resolver.default_threshold
            validate_range(effective_threshold, "threshold", min_val=0, max_val=100)

            matches = await resolver.resolve_group(query, effective_threshold)
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
    async def resolve_category(query: str, threshold: Optional[int] = None) -> List[Dict[str, Any]]:
        """Fuzzy-match an expense category by name (e.g. "food", "utilities").
        Returns matches with id, name, and match_score. Searches subcategories too."""
        try:
            validate_required(query, "query")
            effective_threshold = threshold if threshold is not None else resolver.default_threshold
            validate_range(effective_threshold, "threshold", min_val=0, max_val=100)

            matches = await resolver.resolve_category(query, effective_threshold)
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
        """Add a comment to an expense. Visible to all users in the expense."""
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
        """Get all comments on an expense."""
        try:
            result = await client.get_comments(expense_id)
            logger.info(f"Retrieved comments for expense {expense_id}")
            return result
        except Exception as e:
            logger.error(f"Error getting comments for expense {expense_id}: {e}")
            raise
    
    @mcp.tool()
    async def delete_comment(comment_id: int) -> Dict[str, Any]:
        """Delete a comment. You can only delete your own comments."""
        try:
            result = await client.delete_comment(comment_id)
            logger.info(f"Deleted comment {comment_id}")
            return result
        except Exception as e:
            logger.error(f"Error deleting comment {comment_id}: {e}")
            raise


# ============================================================================
# Notification Tools
# ============================================================================

def register_notification_tools(mcp: FastMCP) -> None:
    """Register notification-related MCP tools."""

    @mcp.tool()
    async def get_notifications() -> Dict[str, Any]:
        """Get recent notifications for the current user (new expenses, payments, comments, group activity)."""
        try:
            result = await client.get_notifications()
            logger.info("Retrieved notifications")
            return result
        except Exception as e:
            logger.error(f"Error getting notifications: {e}")
            raise


# ============================================================================
# Utility Tools
# ============================================================================

def register_utility_tools(mcp: FastMCP) -> None:
    """Register utility MCP tools."""
    
    @mcp.tool()
    async def get_categories() -> Dict[str, Any]:
        """Get all expense categories and subcategories. Results are cached."""
        try:
            result = await client.get_categories()
            logger.info("Retrieved categories")
            return result
        except Exception as e:
            logger.error(f"Error getting categories: {e}")
            raise
    
    @mcp.tool()
    async def get_currencies() -> Dict[str, Any]:
        """Get all supported currency codes and symbols. Results are cached."""
        try:
            result = await client.get_currencies()
            logger.info("Retrieved currencies")
            return result
        except Exception as e:
            logger.error(f"Error getting currencies: {e}")
            raise