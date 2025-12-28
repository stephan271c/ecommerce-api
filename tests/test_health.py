"""
Tests for health check endpoints.
"""

import pytest
from src.schemas.schemas import HealthCheck
from src.schemas.schemas import HealthCheck


class TestHealthCheck:
    """Tests for health check endpoints."""

    def test_health_check(self, client):
        """Test basic health check."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data

    def test_detailed_health_check(self, client):
        """Test detailed health check."""
        response = client.get("/health/detailed")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "database" in data
        assert "redis" in data


class TestRoot:
    """Tests for root endpoint."""

    def test_root_endpoint(self, client):
        """Test root endpoint returns the home page."""
        response = client.get("/")
        
        assert response.status_code == 200
        # Root now serves HTML (Jinja2 frontend home page)
        assert "text/html" in response.headers.get("content-type", "")
