"""Authentication handlers for Splitwise API."""

from typing import Dict, Protocol


class AuthHandler(Protocol):
    """Protocol for authentication handlers."""
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Generate authentication headers for API requests."""
        ...


class OAuth2Handler:
    """Handles OAuth 2.0 authentication with Splitwise.
    
    This handler manages OAuth 2.0 authentication by storing the access token
    and generating the appropriate Authorization header for API requests.
    
    Attributes:
        consumer_key: OAuth consumer key from Splitwise app registration
        consumer_secret: OAuth consumer secret from Splitwise app registration
        access_token: OAuth access token obtained through authorization flow
    """
    
    def __init__(
        self,
        consumer_key: str,
        consumer_secret: str,
        access_token: str
    ):
        """Initialize OAuth2Handler with credentials.
        
        Args:
            consumer_key: OAuth consumer key
            consumer_secret: OAuth consumer secret
            access_token: OAuth access token
        """
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.access_token = access_token
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Generate authentication headers for API requests.
        
        Returns:
            Dictionary containing Authorization header with Bearer token
        """
        return {
            "Authorization": f"Bearer {self.access_token}"
        }


class APIKeyHandler:
    """Handles API Key authentication with Splitwise.
    
    This handler manages API key authentication by storing the API key
    and generating the appropriate Authorization header for API requests.
    
    Attributes:
        api_key: API key from Splitwise
    """
    
    def __init__(self, api_key: str):
        """Initialize APIKeyHandler with API key.
        
        Args:
            api_key: Splitwise API key
        """
        self.api_key = api_key
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Generate authentication headers for API requests.
        
        Returns:
            Dictionary containing Authorization header with API key
        """
        return {
            "Authorization": f"Bearer {self.api_key}"
        }
