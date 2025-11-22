"""Caching layer for Splitwise MCP Server."""

import time
import logging
from typing import Any, Optional, Dict

logger = logging.getLogger(__name__)


class CacheManager:
    """Manages caching of frequently accessed data with TTL support.
    
    This cache manager provides a simple in-memory cache with time-to-live (TTL)
    support for cache entries. It's designed to reduce API calls for static or
    semi-static data like categories and currencies.
    
    Attributes:
        ttl_seconds: Time-to-live for cache entries in seconds
        _cache: Internal dictionary storing cached values
        _timestamps: Dictionary tracking when each entry was cached
    """
    
    def __init__(self, ttl_seconds: int = 86400):
        """Initialize cache manager with TTL.
        
        Args:
            ttl_seconds: Time-to-live for cache entries in seconds (default: 86400 = 24 hours)
        """
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, Any] = {}
        self._timestamps: Dict[str, float] = {}
        logger.info(f"CacheManager initialized with TTL: {ttl_seconds} seconds")
    
    def get(self, key: str) -> Optional[Any]:
        """Retrieve cached value if not expired.
        
        Args:
            key: Cache key to retrieve
            
        Returns:
            Cached value if exists and not expired, None otherwise
        """
        if key not in self._cache:
            logger.debug(f"Cache miss: {key}")
            return None
        
        # Check if cache entry has expired
        timestamp = self._timestamps.get(key, 0)
        current_time = time.time()
        age = current_time - timestamp
        
        if age > self.ttl_seconds:
            logger.debug(f"Cache expired: {key} (age: {age:.1f}s, TTL: {self.ttl_seconds}s)")
            # Remove expired entry
            del self._cache[key]
            del self._timestamps[key]
            return None
        
        logger.debug(f"Cache hit: {key} (age: {age:.1f}s)")
        return self._cache[key]
    
    def set(self, key: str, value: Any) -> None:
        """Store value in cache with current timestamp.
        
        Args:
            key: Cache key to store
            value: Value to cache
        """
        self._cache[key] = value
        self._timestamps[key] = time.time()
        logger.debug(f"Cache set: {key}")
    
    def clear(self, key: Optional[str] = None) -> None:
        """Clear cached data.
        
        Args:
            key: Specific key to clear. If None, clears all cache entries.
        """
        if key is None:
            # Clear all cache entries
            count = len(self._cache)
            self._cache.clear()
            self._timestamps.clear()
            logger.info(f"Cache cleared: {count} entries removed")
        else:
            # Clear specific key
            if key in self._cache:
                del self._cache[key]
                del self._timestamps[key]
                logger.debug(f"Cache cleared: {key}")
            else:
                logger.debug(f"Cache clear attempted for non-existent key: {key}")
    
    def invalidate_expired(self) -> int:
        """Remove all expired entries from cache.
        
        Returns:
            Number of entries removed
        """
        current_time = time.time()
        expired_keys = []
        
        for key, timestamp in self._timestamps.items():
            age = current_time - timestamp
            if age > self.ttl_seconds:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self._cache[key]
            del self._timestamps[key]
        
        if expired_keys:
            logger.info(f"Invalidated {len(expired_keys)} expired cache entries")
        
        return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Dictionary containing cache statistics:
            - total_entries: Number of cached entries
            - ttl_seconds: Configured TTL
            - entries: List of cache keys with their ages
        """
        current_time = time.time()
        entries = []
        
        for key in self._cache.keys():
            timestamp = self._timestamps.get(key, 0)
            age = current_time - timestamp
            entries.append({
                "key": key,
                "age_seconds": round(age, 2),
                "expired": age > self.ttl_seconds
            })
        
        return {
            "total_entries": len(self._cache),
            "ttl_seconds": self.ttl_seconds,
            "entries": entries
        }
