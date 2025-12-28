"""
Tests for rate limiting functionality.
"""

import pytest
from unittest.mock import patch, MagicMock
import time


class TestRateLimiting:
    """Tests for rate limiting."""

    def test_rate_limit_headers_present(self, client, test_user, auth_header):
        """Test that rate limit headers are present in response."""
        response = client.get("/v1/rate-limited")
        
        # Check response includes rate limit info
        assert response.status_code == 200
        data = response.json()
        assert "rate_limit" in data
        assert "limit" in data["rate_limit"]
        assert "remaining" in data["rate_limit"]
        assert "reset" in data["rate_limit"]

    def test_rate_limit_decrements(self, client):
        """Test that remaining count decrements with each request."""
        # Make first request
        response1 = client.get("/v1/rate-limited")
        assert response1.status_code == 200
        remaining1 = response1.json()["rate_limit"]["remaining"]
        
        # Make second request
        response2 = client.get("/v1/rate-limited")
        assert response2.status_code == 200
        remaining2 = response2.json()["rate_limit"]["remaining"]
        
        # Remaining should decrease
        assert remaining2 < remaining1


class TestRateLimitFunctions:
    """Tests for rate limit utility functions."""

    def test_get_client_identifier_with_forwarded_for(self):
        """Test client identifier extraction from X-Forwarded-For header."""
        from src.services.rate_limit import get_client_identifier
        
        mock_request = MagicMock()
        mock_request.headers.get.return_value = "203.0.113.195, 70.41.3.18"
        mock_request.client.host = "127.0.0.1"
        
        client_id = get_client_identifier(mock_request)
        assert client_id == "203.0.113.195"

    def test_get_client_identifier_without_forwarded_for(self):
        """Test client identifier extraction from direct client."""
        from src.services.rate_limit import get_client_identifier
        
        mock_request = MagicMock()
        mock_request.headers.get.return_value = None
        mock_request.client.host = "192.168.1.1"
        
        client_id = get_client_identifier(mock_request)
        assert client_id == "192.168.1.1"

    def test_memory_rate_limit_allows_under_limit(self):
        """Test in-memory rate limiting allows requests under limit."""
        from src.services.rate_limit import _memory_rate_limit, _memory_storage
        
        # Clear memory storage
        _memory_storage.clear()
        
        is_allowed, remaining, limit, reset_time = _memory_rate_limit(
            client_id="test_client",
            limit=10,
            window_seconds=60,
            current_time=time.time()
        )
        
        assert is_allowed is True
        assert remaining == 9
        assert limit == 10

    def test_memory_rate_limit_blocks_over_limit(self):
        """Test in-memory rate limiting blocks requests over limit."""
        from src.services.rate_limit import _memory_rate_limit, _memory_storage
        
        # Clear and fill up memory storage
        _memory_storage.clear()
        current_time = time.time()
        _memory_storage["over_limit_client"] = [current_time - i for i in range(10)]
        
        is_allowed, remaining, limit, reset_time = _memory_rate_limit(
            client_id="over_limit_client",
            limit=10,
            window_seconds=60,
            current_time=current_time
        )
        
        assert is_allowed is False
        assert remaining == 0

    def test_sliding_window_rate_limit_without_redis(self):
        """Test sliding window falls back to memory when Redis unavailable."""
        from src.services.rate_limit import (
            sliding_window_rate_limit, 
            get_client_identifier,
            _memory_storage,
            _memory_rate_limit
        )
        from src.core.exceptions import RateLimitError

        # Clear memory storage
        _memory_storage.clear()
        
        with patch('src.services.rate_limit.get_redis_client', return_value=None):
            is_allowed, remaining, limit, reset_time = sliding_window_rate_limit(
                client_id="memory_fallback_test",
                limit=100,
                window_seconds=60
            )
            
            assert is_allowed is True
            assert remaining >= 0
            assert limit == 100


class TestRateLimitError:
    """Tests for rate limit error responses."""

    def test_rate_limit_error_format(self):
        """Test RateLimitError produces correct error format."""
        from src.core.exceptions import RateLimitError
        
        error = RateLimitError(retry_after=30)
        
        assert error.status_code == 429
        assert error.detail["error_code"] == "RATE_LIMIT_EXCEEDED"
        assert error.detail["details"]["retry_after"] == 30
