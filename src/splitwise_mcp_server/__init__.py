"""Splitwise MCP Server - Model Context Protocol server for Splitwise API."""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from splitwise_mcp_server.auth import OAuth2Handler, APIKeyHandler
from splitwise_mcp_server.config import SplitwiseConfig
from splitwise_mcp_server.cache import CacheManager
from splitwise_mcp_server.resolver import EntityResolver

__all__ = [
    "SplitwiseConfig",
    "OAuth2Handler",
    "APIKeyHandler",
    "CacheManager",
    "EntityResolver",
    "__version__",
]
