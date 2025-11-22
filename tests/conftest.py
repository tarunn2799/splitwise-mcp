"""Pytest configuration and fixtures."""

import pytest


@pytest.fixture
def sample_config():
    """Sample configuration for testing."""
    from splitwise_mcp_server.config import SplitwiseConfig
    
    return SplitwiseConfig(
        oauth_consumer_key="test_key",
        oauth_consumer_secret="test_secret",
        oauth_access_token="test_token",
        cache_ttl_seconds=3600,
        default_match_threshold=70,
    )
