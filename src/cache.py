"""
Redis-based caching implementation.

Provides caching functionality with Redis as primary storage
and in-memory fallback when Redis is unavailable.
"""

import json
import time
from typing import Optional, Any, Callable
from functools import wraps
import redis

from .config import get_settings

settings = get_settings()

# In-memory cache fallback
_memory_cache: dict[str, tuple[Any, float]] = {}

# Redis client (lazy initialization)
_redis_client: Optional[redis.Redis] = None


def get_redis_client() -> Optional[redis.Redis]:
    """Get or create Redis client for caching."""
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_timeout=1.0,
                socket_connect_timeout=1.0
            )
            _redis_client.ping()
        except (redis.ConnectionError, redis.TimeoutError):
            _redis_client = None
    return _redis_client


def get_cache(key: str) -> Optional[Any]:
    """
    Get a value from cache.
    
    Args:
        key: Cache key
        
    Returns:
        Cached value or None if not found/expired
    """
    redis_client = get_redis_client()
    
    if redis_client:
        try:
            value = redis_client.get(f"cache:{key}")
            if value:
                return json.loads(value)
        except redis.RedisError:
            pass
    
    # Fallback to memory cache
    if key in _memory_cache:
        value, expires_at = _memory_cache[key]
        if time.time() < expires_at:
            return value
        else:
            del _memory_cache[key]
    
    return None


def set_cache(key: str, value: Any, ttl_seconds: int = 60) -> bool:
    """
    Set a value in cache.
    
    Args:
        key: Cache key
        value: Value to cache (must be JSON serializable)
        ttl_seconds: Time to live in seconds (default: 60)
        
    Returns:
        True if cached successfully
    """
    redis_client = get_redis_client()
    
    if redis_client:
        try:
            redis_client.setex(
                f"cache:{key}",
                ttl_seconds,
                json.dumps(value)
            )
            return True
        except redis.RedisError:
            pass
    
    # Fallback to memory cache
    _memory_cache[key] = (value, time.time() + ttl_seconds)
    return True


def invalidate_cache(pattern: str) -> int:
    """
    Invalidate cache entries matching a pattern.
    
    Args:
        pattern: Key pattern (supports * wildcard for Redis)
        
    Returns:
        Number of keys invalidated
    """
    count = 0
    redis_client = get_redis_client()
    
    if redis_client:
        try:
            keys = redis_client.keys(f"cache:{pattern}")
            if keys:
                count = redis_client.delete(*keys)
        except redis.RedisError:
            pass
    
    # Also clean memory cache
    keys_to_delete = [
        k for k in _memory_cache.keys()
        if pattern.replace("*", "") in k
    ]
    for k in keys_to_delete:
        del _memory_cache[k]
        count += 1
    
    return count


def cached(ttl_seconds: int = 60, key_prefix: str = ""):
    """
    Decorator for caching function results.
    
    Args:
        ttl_seconds: Cache TTL in seconds
        key_prefix: Prefix for cache key
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Build cache key from function name and arguments
            cache_key = f"{key_prefix}:{func.__name__}"
            if kwargs:
                # Sort kwargs for consistent key
                sorted_kwargs = sorted(kwargs.items())
                cache_key += ":" + ":".join(f"{k}={v}" for k, v in sorted_kwargs)
            
            # Try to get from cache
            cached_value = get_cache(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Call function and cache result
            result = await func(*args, **kwargs)
            
            # Convert Pydantic models to dict for caching
            if hasattr(result, "model_dump"):
                cacheable = result.model_dump(mode='json')
            else:
                cacheable = result
            
            set_cache(cache_key, cacheable, ttl_seconds)
            return result
        
        return wrapper
    return decorator
