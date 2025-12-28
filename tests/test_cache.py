"""
Tests for caching functionality.
"""

import pytest
from unittest.mock import patch, MagicMock
import time


class TestCacheFunctions:
    """Tests for cache utility functions."""

    def test_set_and_get_memory_cache(self):
        """Test setting and getting from memory cache."""
        from src.cache import set_cache, get_cache, _memory_cache
        
        # Clear memory cache
        _memory_cache.clear()
        
        with patch('src.cache.get_redis_client', return_value=None):
            # Set value
            result = set_cache("test_key", {"value": 123}, ttl_seconds=60)
            assert result is True
            
            # Get value
            cached = get_cache("test_key")
            assert cached == {"value": 123}

    def test_cache_expiration(self):
        """Test that cache entries expire."""
        from src.cache import set_cache, get_cache, _memory_cache
        
        # Clear memory cache
        _memory_cache.clear()
        
        with patch('src.cache.get_redis_client', return_value=None):
            # Set value with very short TTL
            set_cache("expire_test", {"data": "test"}, ttl_seconds=1)
            
            # Should be present immediately
            assert get_cache("expire_test") == {"data": "test"}
            
            # Manually expire it
            key = "expire_test"
            if key in _memory_cache:
                value, _ = _memory_cache[key]
                _memory_cache[key] = (value, time.time() - 1)
            
            # Should be expired now
            assert get_cache("expire_test") is None

    def test_invalidate_cache(self):
        """Test cache invalidation."""
        from src.cache import set_cache, get_cache, invalidate_cache, _memory_cache
        
        # Clear memory cache
        _memory_cache.clear()
        
        with patch('src.cache.get_redis_client', return_value=None):
            # Set multiple values
            set_cache("listing:1", {"id": 1}, ttl_seconds=60)
            set_cache("listing:2", {"id": 2}, ttl_seconds=60)
            set_cache("user:1", {"id": 1}, ttl_seconds=60)
            
            # Invalidate listing cache
            count = invalidate_cache("listing")
            
            # Listings should be gone
            assert get_cache("listing:1") is None
            assert get_cache("listing:2") is None
            
            # User should still be present
            assert get_cache("user:1") == {"id": 1}

    def test_get_cache_returns_none_for_missing(self):
        """Test that get_cache returns None for missing keys."""
        from src.cache import get_cache, _memory_cache
        
        _memory_cache.clear()
        
        with patch('src.cache.get_redis_client', return_value=None):
            result = get_cache("nonexistent_key")
            assert result is None


class TestCacheDecorator:
    """Tests for the cached decorator."""

    @pytest.mark.asyncio
    async def test_cached_decorator(self):
        """Test the cached decorator caches function results."""
        from src.cache import cached, _memory_cache
        
        _memory_cache.clear()
        call_count = 0
        
        @cached(ttl_seconds=60, key_prefix="test")
        async def expensive_function(param: str):
            nonlocal call_count
            call_count += 1
            return {"result": param}
        
        with patch('src.cache.get_redis_client', return_value=None):
            # First call should execute function
            result1 = await expensive_function(param="value1")
            assert call_count == 1
            assert result1 == {"result": "value1"}
            
            # Second call should return cached
            result2 = await expensive_function(param="value1")
            assert call_count == 1  # Not called again
            assert result2 == {"result": "value1"}
