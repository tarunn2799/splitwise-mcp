"""Splitwise API client implementation."""

import logging
from typing import Any, Dict, Optional, Union
import httpx

from .auth import AuthHandler, OAuth2Handler, APIKeyHandler
from .errors import MCPError, RateLimitError
from .cache import CacheManager

logger = logging.getLogger(__name__)


class SplitwiseClient:
    """Main client for Splitwise API interactions.
    
    This client handles all HTTP communication with the Splitwise API,
    including authentication, error handling, and request/response logging.
    
    Attributes:
        BASE_URL: Base URL for Splitwise API v3.0
        auth_handler: Authentication handler (OAuth2 or API Key)
        client: Async HTTP client with connection pooling
    """
    
    BASE_URL = "https://secure.splitwise.com/api/v3.0"
    
    def __init__(self, auth_handler: Union[OAuth2Handler, APIKeyHandler], cache_ttl: int = 86400):
        """Initialize SplitwiseClient with authentication handler.
        
        Args:
            auth_handler: Authentication handler for API requests
            cache_ttl: Time-to-live for cache entries in seconds (default: 86400 = 24 hours)
        """
        self.auth_handler = auth_handler
        self.client = httpx.AsyncClient(
            timeout=30.0,
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )
        self.cache = CacheManager(ttl_seconds=cache_ttl)
    
    async def close(self):
        """Close the HTTP client and cleanup resources."""
        await self.client.aclose()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests including authentication.
        
        Returns:
            Dictionary of HTTP headers
        """
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        headers.update(self.auth_handler.get_auth_headers())
        return headers
    
    def _log_request(self, method: str, url: str, params: Optional[Dict] = None):
        """Log API request without exposing credentials.
        
        Args:
            method: HTTP method
            url: Request URL
            params: Query parameters
        """
        logger.debug(f"API Request: {method} {url}")
        if params:
            logger.debug(f"Parameters: {params}")
    
    def _log_response(self, response: httpx.Response):
        """Log API response without exposing sensitive data.
        
        Args:
            response: HTTP response object
        """
        logger.debug(f"API Response: {response.status_code}")
    
    def handle_api_error(self, response: httpx.Response) -> MCPError:
        """Convert HTTP errors to structured MCP errors.
        
        Args:
            response: HTTP response with error status
            
        Returns:
            MCPError with structured error information
            
        Raises:
            RateLimitError: If rate limit is exceeded (429 status)
        """
        # Extract retry-after header for rate limiting
        retry_after = None
        if response.status_code == 429:
            retry_after_header = response.headers.get("Retry-After")
            if retry_after_header:
                try:
                    retry_after = int(retry_after_header)
                except ValueError:
                    pass
        
        # Enhanced error messages with specific guidance
        error_map = {
            401: (
                "authentication",
                "Authentication failed. Please check your credentials:\n"
                "- For OAuth: Verify SPLITWISE_OAUTH_ACCESS_TOKEN is set correctly\n"
                "- For API Key: Verify SPLITWISE_API_KEY is set correctly\n"
                "- Token may have expired - generate a new access token"
            ),
            403: (
                "authorization",
                "Access forbidden. You don't have permission to access this resource.\n"
                "This may occur if:\n"
                "- You're trying to access another user's private data\n"
                "- You're not a member of the specified group\n"
                "- The resource has been deleted or you've been removed"
            ),
            404: (
                "not_found",
                "Resource not found. The requested item doesn't exist or has been deleted.\n"
                "Please verify:\n"
                "- The ID is correct\n"
                "- You have access to this resource\n"
                "- The resource hasn't been deleted"
            ),
            400: (
                "validation",
                "Invalid request parameters. Please check your input:\n"
                "- Required fields may be missing\n"
                "- Field values may be in the wrong format\n"
                "- Numeric values may be out of range"
            ),
            429: (
                "rate_limit",
                f"Rate limit exceeded. Too many requests in a short time.\n"
                f"{'Wait ' + str(retry_after) + ' seconds before retrying.' if retry_after else 'Please wait a few minutes before retrying.'}\n"
                "Tips to avoid rate limits:\n"
                "- Reduce request frequency\n"
                "- Use caching for frequently accessed data\n"
                "- Batch operations when possible"
            ),
            500: (
                "server_error",
                "Splitwise API internal error. This is a temporary issue on Splitwise's side.\n"
                "Please try again in a few moments."
            ),
            502: (
                "server_error",
                "Bad gateway. Splitwise API may be temporarily unavailable.\n"
                "Please try again in a few minutes."
            ),
            503: (
                "server_error",
                "Service unavailable. Splitwise is temporarily down for maintenance.\n"
                "Please try again later."
            ),
        }
        
        error_type, default_message = error_map.get(
            response.status_code,
            ("unknown", f"An unexpected error occurred (HTTP {response.status_code}).")
        )
        
        # Try to extract detailed error information from response
        try:
            error_data = response.json()
            
            # Handle different error response formats
            if isinstance(error_data, dict):
                # Check for 'error' or 'errors' field
                api_message = error_data.get("error") or error_data.get("errors")
                
                if api_message:
                    if isinstance(api_message, dict):
                        # Format nested error messages
                        error_parts = []
                        for key, value in api_message.items():
                            if isinstance(value, list):
                                error_parts.append(f"{key}: {', '.join(str(v) for v in value)}")
                            else:
                                error_parts.append(f"{key}: {value}")
                        api_message = "; ".join(error_parts)
                    elif isinstance(api_message, list):
                        api_message = "; ".join(str(m) for m in api_message)
                    
                    # Combine API message with guidance
                    message = f"{api_message}\n\n{default_message}"
                else:
                    message = default_message
                
                details = error_data
            else:
                message = default_message
                details = {"response": str(error_data)}
        except Exception:
            message = default_message
            details = {"response_text": response.text[:200] if response.text else ""}
        
        # Add retry-after to details if available
        if retry_after:
            details["retry_after_seconds"] = retry_after
        
        logger.error(f"API Error: {response.status_code} - {message}")
        
        # Raise RateLimitError for 429 status
        if response.status_code == 429:
            raise RateLimitError(message, retry_after=retry_after)
        
        return MCPError(
            error_type=error_type,
            message=message,
            status_code=response.status_code,
            details=details
        )
    
    async def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make GET request to Splitwise API.
        
        Args:
            endpoint: API endpoint path (e.g., "/get_current_user")
            params: Optional query parameters
            
        Returns:
            JSON response as dictionary
            
        Raises:
            RateLimitError: If rate limit is exceeded
            Exception: If request fails with error details
        """
        url = f"{self.BASE_URL}{endpoint}"
        headers = self._get_headers()
        
        self._log_request("GET", url, params)
        
        try:
            response = await self.client.get(url, headers=headers, params=params)
            self._log_response(response)
            
            if response.status_code >= 400:
                # handle_api_error will raise RateLimitError for 429
                error = self.handle_api_error(response)
                raise Exception(f"{error.message} (Status: {error.status_code})")
            
            return response.json()
        except RateLimitError:
            # Re-raise rate limit errors without wrapping
            raise
        except httpx.RequestError as e:
            logger.error(f"Network error: {str(e)}")
            raise Exception(f"Network error: Could not connect to Splitwise API. Please check your internet connection.\nDetails: {str(e)}")
    
    def _flatten_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Flatten nested data structures for Splitwise API.
        
        Splitwise API expects flattened keys like users__0__user_id instead of nested arrays.
        
        Args:
            data: Dictionary potentially containing nested arrays
            
        Returns:
            Flattened dictionary with Splitwise-compatible keys
        """
        flattened = {}
        for key, value in data.items():
            if key == "users" and isinstance(value, list):
                # Flatten users array
                for i, user in enumerate(value):
                    for user_key, user_value in user.items():
                        flattened[f"users__{i}__{user_key}"] = str(user_value)
            elif isinstance(value, bool):
                # Convert booleans to lowercase strings
                flattened[key] = str(value).lower()
            else:
                flattened[key] = value
        return flattened
    
    async def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make POST request to Splitwise API.
        
        Args:
            endpoint: API endpoint path
            data: Optional request body data
            
        Returns:
            JSON response as dictionary
            
        Raises:
            RateLimitError: If rate limit is exceeded
            Exception: If request fails with error details
        """
        url = f"{self.BASE_URL}{endpoint}"
        headers = self._get_headers()
        
        self._log_request("POST", url)
        
        # Flatten data for Splitwise API format
        if data:
            data = self._flatten_data(data)
        
        try:
            response = await self.client.post(url, headers=headers, json=data)
            self._log_response(response)
            
            if response.status_code >= 400:
                # handle_api_error will raise RateLimitError for 429
                error = self.handle_api_error(response)
                raise Exception(f"{error.message} (Status: {error.status_code})")
            
            return response.json()
        except RateLimitError:
            # Re-raise rate limit errors without wrapping
            raise
        except httpx.RequestError as e:
            logger.error(f"Network error: {str(e)}")
            raise Exception(f"Network error: Could not connect to Splitwise API. Please check your internet connection.\nDetails: {str(e)}")
    
    async def put(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make PUT request to Splitwise API.
        
        Args:
            endpoint: API endpoint path
            data: Optional request body data
            
        Returns:
            JSON response as dictionary
            
        Raises:
            RateLimitError: If rate limit is exceeded
            Exception: If request fails with error details
        """
        url = f"{self.BASE_URL}{endpoint}"
        headers = self._get_headers()
        
        self._log_request("PUT", url)
        
        # Flatten data for Splitwise API format
        if data:
            data = self._flatten_data(data)
        
        try:
            response = await self.client.put(url, headers=headers, json=data)
            self._log_response(response)
            
            if response.status_code >= 400:
                # handle_api_error will raise RateLimitError for 429
                error = self.handle_api_error(response)
                raise Exception(f"{error.message} (Status: {error.status_code})")
            
            return response.json()
        except RateLimitError:
            # Re-raise rate limit errors without wrapping
            raise
        except httpx.RequestError as e:
            logger.error(f"Network error: {str(e)}")
            raise Exception(f"Network error: Could not connect to Splitwise API. Please check your internet connection.\nDetails: {str(e)}")
    
    async def delete(self, endpoint: str) -> Dict[str, Any]:
        """Make DELETE request to Splitwise API.
        
        Args:
            endpoint: API endpoint path
            
        Returns:
            JSON response as dictionary
            
        Raises:
            RateLimitError: If rate limit is exceeded
            Exception: If request fails with error details
        """
        url = f"{self.BASE_URL}{endpoint}"
        headers = self._get_headers()
        
        self._log_request("DELETE", url)
        
        try:
            response = await self.client.delete(url, headers=headers)
            self._log_response(response)
            
            if response.status_code >= 400:
                # handle_api_error will raise RateLimitError for 429
                error = self.handle_api_error(response)
                raise Exception(f"{error.message} (Status: {error.status_code})")
            
            # DELETE may return empty response
            if response.text:
                return response.json()
            return {"success": True}
        except RateLimitError:
            # Re-raise rate limit errors without wrapping
            raise
        except httpx.RequestError as e:
            logger.error(f"Network error: {str(e)}")
            raise Exception(f"Network error: Could not connect to Splitwise API. Please check your internet connection.\nDetails: {str(e)}")

    # User endpoints
    
    async def get_current_user(self) -> Dict[str, Any]:
        """Get current authenticated user information.
        
        Returns:
            Dictionary containing user profile information including:
            - id: User ID
            - first_name: User's first name
            - last_name: User's last name
            - email: User's email address
            - registration_status: Registration status
            - picture: Profile picture information
            
        Raises:
            Exception: If request fails
        """
        return await self.get("/get_current_user")
    
    async def get_user(self, user_id: int) -> Dict[str, Any]:
        """Get information about a specific user.
        
        Args:
            user_id: ID of the user to retrieve
            
        Returns:
            Dictionary containing user information
            
        Raises:
            Exception: If request fails or user not found
        """
        return await self.get(f"/get_user/{user_id}")

    # Expense endpoints
    
    async def get_expenses(
        self,
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
        
        Args:
            group_id: Filter by group ID
            friend_id: Filter by friend user ID
            dated_after: Filter expenses dated after this date (ISO 8601)
            dated_before: Filter expenses dated before this date (ISO 8601)
            updated_after: Filter expenses updated after this date (ISO 8601)
            updated_before: Filter expenses updated before this date (ISO 8601)
            limit: Maximum number of expenses to return (default: 20)
            offset: Number of expenses to skip for pagination (default: 0)
            
        Returns:
            Dictionary containing list of expenses
            
        Raises:
            Exception: If request fails
        """
        params = {
            "limit": limit,
            "offset": offset
        }
        
        if group_id is not None:
            params["group_id"] = group_id
        if friend_id is not None:
            params["friend_id"] = friend_id
        if dated_after:
            params["dated_after"] = dated_after
        if dated_before:
            params["dated_before"] = dated_before
        if updated_after:
            params["updated_after"] = updated_after
        if updated_before:
            params["updated_before"] = updated_before
        
        return await self.get("/get_expenses", params=params)
    
    async def get_expense(self, expense_id: int) -> Dict[str, Any]:
        """Get detailed information about a specific expense.
        
        Args:
            expense_id: ID of the expense to retrieve
            
        Returns:
            Dictionary containing expense details including:
            - id: Expense ID
            - description: Expense description
            - cost: Total cost
            - currency_code: Currency code
            - date: Expense date
            - category: Category information
            - users: List of users involved in the split
            
        Raises:
            Exception: If request fails or expense not found
        """
        return await self.get(f"/get_expense/{expense_id}")
    
    async def create_expense(self, expense_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new expense.
        
        Args:
            expense_data: Dictionary containing expense information:
                - cost: Amount as string (e.g., "25.50")
                - description: Expense description
                - date: ISO 8601 datetime string (optional, defaults to now)
                - currency_code: Currency code (optional, defaults to USD)
                - category_id: Category ID (optional)
                - group_id: Group ID (optional, 0 for non-group expense)
                - users: List of user split information (optional)
                - split_equally: Boolean to split equally (optional)
                
        Returns:
            Dictionary containing created expense information
            
        Raises:
            Exception: If request fails or validation errors occur
        """
        return await self.post("/create_expense", data=expense_data)
    
    async def update_expense(self, expense_id: int, expense_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing expense.
        
        Args:
            expense_id: ID of the expense to update
            expense_data: Dictionary containing fields to update:
                - cost: New amount as string (optional)
                - description: New description (optional)
                - date: New date (optional)
                - category_id: New category ID (optional)
                - users: Updated user split information (optional)
                
        Returns:
            Dictionary containing updated expense information
            
        Raises:
            Exception: If request fails or expense not found
        """
        return await self.post(f"/update_expense/{expense_id}", data=expense_data)
    
    async def delete_expense(self, expense_id: int) -> Dict[str, Any]:
        """Delete an expense.
        
        Args:
            expense_id: ID of the expense to delete
            
        Returns:
            Dictionary with success status
            
        Raises:
            Exception: If request fails or expense not found
        """
        return await self.post(f"/delete_expense/{expense_id}")

    # Group endpoints
    
    async def get_groups(self) -> Dict[str, Any]:
        """Get all groups for the current user.
        
        Returns:
            Dictionary containing list of groups with:
            - id: Group ID
            - name: Group name
            - members: List of group members
            - simplify_by_default: Whether debt simplification is enabled
            
        Raises:
            Exception: If request fails
        """
        return await self.get("/get_groups")
    
    async def get_group(self, group_id: int) -> Dict[str, Any]:
        """Get detailed information about a specific group.
        
        Args:
            group_id: ID of the group to retrieve
            
        Returns:
            Dictionary containing group details including:
            - id: Group ID
            - name: Group name
            - members: List of members with balance information
            - simplify_by_default: Debt simplification setting
            - original_debts: List of debts before simplification
            - simplified_debts: List of simplified debts
            
        Raises:
            Exception: If request fails or group not found
        """
        return await self.get(f"/get_group/{group_id}")
    
    async def create_group(self, group_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new group.
        
        Args:
            group_data: Dictionary containing group information:
                - name: Group name (required)
                - group_type: Type of group (home, trip, couple, other)
                - simplify_by_default: Enable debt simplification (optional)
                - users: List of initial members with user_id (optional)
                
        Returns:
            Dictionary containing created group information
            
        Raises:
            Exception: If request fails or validation errors occur
        """
        return await self.post("/create_group", data=group_data)
    
    async def delete_group(self, group_id: int) -> Dict[str, Any]:
        """Delete a group.
        
        Args:
            group_id: ID of the group to delete
            
        Returns:
            Dictionary with success status
            
        Raises:
            Exception: If request fails or group not found
        """
        return await self.post(f"/delete_group/{group_id}")
    
    async def add_user_to_group(self, group_id: int, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a user to a group.
        
        Args:
            group_id: ID of the group
            user_data: Dictionary containing user information:
                - user_id: ID of user to add (optional if email/first_name provided)
                - email: Email of user to add (optional)
                - first_name: First name of user (optional)
                - last_name: Last name of user (optional)
                
        Returns:
            Dictionary with success status and updated group information
            
        Raises:
            Exception: If request fails or user/group not found
        """
        return await self.post(f"/add_user_to_group", data={
            "group_id": group_id,
            **user_data
        })
    
    async def remove_user_from_group(self, group_id: int, user_id: int) -> Dict[str, Any]:
        """Remove a user from a group.
        
        Note: User must have zero balance in the group to be removed.
        
        Args:
            group_id: ID of the group
            user_id: ID of the user to remove
            
        Returns:
            Dictionary with success status
            
        Raises:
            Exception: If request fails, user has non-zero balance, or not found
        """
        return await self.post(f"/remove_user_from_group", data={
            "group_id": group_id,
            "user_id": user_id
        })

    # Friend endpoints
    
    async def get_friends(self) -> Dict[str, Any]:
        """Get all friends for the current user.
        
        Returns:
            Dictionary containing list of friends with:
            - id: User ID
            - first_name: Friend's first name
            - last_name: Friend's last name
            - email: Friend's email
            - balance: List of balances in different currencies
            
        Raises:
            Exception: If request fails
        """
        return await self.get("/get_friends")
    
    async def get_friend(self, user_id: int) -> Dict[str, Any]:
        """Get detailed information about a specific friend.
        
        Args:
            user_id: ID of the friend to retrieve
            
        Returns:
            Dictionary containing friend details including:
            - id: User ID
            - first_name: Friend's first name
            - last_name: Friend's last name
            - email: Friend's email
            - balance: Balance information
            - groups: Shared groups
            
        Raises:
            Exception: If request fails or friend not found
        """
        return await self.get(f"/get_friend/{user_id}")

    # Comment endpoints
    
    async def get_comments(self, expense_id: int) -> Dict[str, Any]:
        """Get all comments for a specific expense.
        
        Args:
            expense_id: ID of the expense
            
        Returns:
            Dictionary containing list of comments with:
            - id: Comment ID
            - content: Comment text
            - user: User who created the comment
            - created_at: Timestamp when comment was created
            
        Raises:
            Exception: If request fails or expense not found
        """
        return await self.get(f"/get_comments", params={"expense_id": expense_id})
    
    async def create_comment(self, expense_id: int, content: str) -> Dict[str, Any]:
        """Create a comment on an expense.
        
        Args:
            expense_id: ID of the expense to comment on
            content: Comment text content
            
        Returns:
            Dictionary containing created comment information
            
        Raises:
            Exception: If request fails or expense not found
        """
        return await self.post("/create_comment", data={
            "expense_id": expense_id,
            "content": content
        })
    
    async def delete_comment(self, comment_id: int) -> Dict[str, Any]:
        """Delete a comment.
        
        Args:
            comment_id: ID of the comment to delete
            
        Returns:
            Dictionary with success status
            
        Raises:
            Exception: If request fails or comment not found
        """
        return await self.post(f"/delete_comment/{comment_id}")

    # Utility endpoints
    
    async def get_categories(self) -> Dict[str, Any]:
        """Get all supported expense categories and subcategories.
        
        This method uses caching to minimize API calls. Categories are cached
        according to the configured TTL (default: 24 hours).
        
        Returns:
            Dictionary containing list of categories with:
            - id: Category ID
            - name: Category name
            - subcategories: List of subcategories (if any)
            
        Raises:
            Exception: If request fails
        """
        # Check cache first
        cached_categories = self.cache.get("categories")
        if cached_categories is not None:
            logger.debug("Returning cached categories")
            return cached_categories
        
        # Fetch from API if not cached
        logger.debug("Fetching categories from API")
        categories = await self.get("/get_categories")
        
        # Store in cache
        self.cache.set("categories", categories)
        
        return categories
    
    async def get_currencies(self) -> Dict[str, Any]:
        """Get all supported currency codes.
        
        This method uses caching to minimize API calls. Currencies are cached
        according to the configured TTL (default: 24 hours).
        
        Returns:
            Dictionary containing list of currencies with:
            - currency_code: Three-letter currency code (e.g., USD, EUR)
            - unit: Currency symbol or unit
            
        Raises:
            Exception: If request fails
        """
        # Check cache first
        cached_currencies = self.cache.get("currencies")
        if cached_currencies is not None:
            logger.debug("Returning cached currencies")
            return cached_currencies
        
        # Fetch from API if not cached
        logger.debug("Fetching currencies from API")
        currencies = await self.get("/get_currencies")
        
        # Store in cache
        self.cache.set("currencies", currencies)
        
        return currencies
