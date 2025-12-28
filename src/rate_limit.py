"""
Redis-based rate limiting implementation.

Uses a sliding window algorithm to limit requests per client.
Falls back to in-memory storage if Redis is unavailable.
"""

import time
from typing import Optional, Dict, Tuple
from collections import defaultdict
from fastapi import Request, Response, Depends
import redis

from .config import get_settings
from .exceptions import RateLimitError

settings = get_settings()

# In-memory fallback storage
_memory_storage: Dict[str, list] = defaultdict(list)

# Redis client (lazy initialization)
_redis_client: Optional[redis.Redis] = None


def get_redis_client() -> Optional[redis.Redis]:
    """Get or create Redis client."""
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_timeout=1.0,
                socket_connect_timeout=1.0
            )
            # Test connection
            _redis_client.ping()
        except (redis.ConnectionError, redis.TimeoutError):
            _redis_client = None
    return _redis_client


def get_client_identifier(request: Request) -> str:
    """
    Get a unique identifier for the client.
    
    Uses IP address as default, but could be extended to use
    user ID for authenticated requests.
    """
    # Try to get real IP from proxy headers
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def sliding_window_rate_limit(
    client_id: str,
    limit: int = None,
    window_seconds: int = None
) -> Tuple[bool, int, int, int]:
    """
    Check rate limit using sliding window algorithm.
    
    Args:
        client_id: Unique client identifier
        limit: Max requests allowed in window
        window_seconds: Window size in seconds
        
    Returns:
        Tuple of (is_allowed, remaining, limit, reset_time)
    """
    limit = limit or settings.RATE_LIMIT_REQUESTS
    window_seconds = window_seconds or settings.RATE_LIMIT_WINDOW_SECONDS
    
    current_time = time.time()
    window_start = current_time - window_seconds
    
    redis_client = get_redis_client()
    
    if redis_client:
        # Use Redis for rate limiting
        key = f"rate_limit:{client_id}"
        
        try:
            # Remove old entries and count current ones
            pipe = redis_client.pipeline()
            pipe.zremrangebyscore(key, 0, window_start)
            pipe.zcard(key)
            pipe.zadd(key, {str(current_time): current_time})
            pipe.expire(key, window_seconds)
            results = pipe.execute()
            
            request_count = results[1]
        except redis.RedisError:
            # Fall back to memory on Redis error
            return _memory_rate_limit(client_id, limit, window_seconds, current_time)
    else:
        # Use in-memory fallback
        return _memory_rate_limit(client_id, limit, window_seconds, current_time)
    
    remaining = max(0, limit - request_count - 1)
    reset_time = int(current_time + window_seconds)
    is_allowed = request_count < limit
    
    return is_allowed, remaining, limit, reset_time


def _memory_rate_limit(
    client_id: str,
    limit: int,
    window_seconds: int,
    current_time: float
) -> Tuple[bool, int, int, int]:
    """In-memory rate limiting fallback."""
    window_start = current_time - window_seconds
    
    # Clean old entries
    _memory_storage[client_id] = [
        t for t in _memory_storage[client_id] 
        if t > window_start
    ]
    
    request_count = len(_memory_storage[client_id])
    
    if request_count < limit:
        _memory_storage[client_id].append(current_time)
        remaining = limit - request_count - 1
        is_allowed = True
    else:
        remaining = 0
        is_allowed = False
    
    reset_time = int(current_time + window_seconds)
    return is_allowed, remaining, limit, reset_time


async def rate_limit_dependency(request: Request) -> None:
    """
    FastAPI dependency for rate limiting.
    
    Raises RateLimitError if limit exceeded.
    Adds rate limit headers to response.
    """
    client_id = get_client_identifier(request)
    is_allowed, remaining, limit, reset_time = sliding_window_rate_limit(client_id)
    
    # Store for response headers (will be added by middleware or route)
    request.state.rate_limit_remaining = remaining
    request.state.rate_limit_limit = limit
    request.state.rate_limit_reset = reset_time
    
    if not is_allowed:
        retry_after = reset_time - int(time.time())
        raise RateLimitError(retry_after=retry_after)


def add_rate_limit_headers(response: Response, request: Request) -> Response:
    """Add rate limit headers to response."""
    if hasattr(request.state, "rate_limit_limit"):
        response.headers["X-RateLimit-Limit"] = str(request.state.rate_limit_limit)
        response.headers["X-RateLimit-Remaining"] = str(request.state.rate_limit_remaining)
        response.headers["X-RateLimit-Reset"] = str(request.state.rate_limit_reset)
    return response
