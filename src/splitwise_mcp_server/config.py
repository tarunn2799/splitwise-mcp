"""Configuration management for Splitwise MCP Server."""

import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv


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
    
    # Logging
    log_level: str = "INFO"
    
    @classmethod
    def from_env(cls) -> "SplitwiseConfig":
        """Load configuration from environment variables."""
        load_dotenv()
        
        config = cls(
            oauth_consumer_key=os.getenv("SPLITWISE_OAUTH_CONSUMER_KEY"),
            oauth_consumer_secret=os.getenv("SPLITWISE_OAUTH_CONSUMER_SECRET"),
            oauth_access_token=os.getenv("SPLITWISE_OAUTH_ACCESS_TOKEN"),
            api_key=os.getenv("SPLITWISE_API_KEY"),
            cache_ttl_seconds=int(os.getenv("SPLITWISE_CACHE_TTL", "86400")),
            default_match_threshold=int(os.getenv("SPLITWISE_MATCH_THRESHOLD", "70")),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
        )
        
        # Validate that at least one authentication method is configured
        has_oauth = all([
            config.oauth_consumer_key,
            config.oauth_consumer_secret,
            config.oauth_access_token
        ])
        has_api_key = config.api_key is not None
        
        if not (has_oauth or has_api_key):
            raise ValueError(
                "No authentication method configured. "
                "Please provide either OAuth credentials "
                "(SPLITWISE_OAUTH_CONSUMER_KEY, SPLITWISE_OAUTH_CONSUMER_SECRET, "
                "SPLITWISE_OAUTH_ACCESS_TOKEN) or API key (SPLITWISE_API_KEY)."
            )
        
        return config
    
    def has_oauth(self) -> bool:
        """Check if OAuth authentication is configured."""
        return all([
            self.oauth_consumer_key,
            self.oauth_consumer_secret,
            self.oauth_access_token
        ])
    
    def has_api_key(self) -> bool:
        """Check if API key authentication is configured."""
        return self.api_key is not None
