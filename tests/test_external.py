"""
Tests for external API endpoints (async HTTP and background tasks).
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock


class TestRandomUserEndpoint:
    """Tests for the random user external API endpoint."""

    def test_random_user_endpoint_exists(self, client):
        """Test the random user endpoint is accessible."""
        # This will call the actual external API
        # In a real test setup, you'd mock httpx
        response = client.get("/v1/external/random-user")
        
        assert response.status_code == 200
        data = response.json()
        assert "source" in data
        assert data["source"] == "randomuser.me"

    @patch('src.routers.external.fetch_random_user')
    def test_random_user_success_mocked(self, mock_fetch, client):
        """Test random user endpoint with mocked external call."""
        mock_fetch.return_value = {
            "results": [{"name": {"first": "John", "last": "Doe"}}]
        }
        
        response = client.get("/v1/external/random-user")
        
        assert response.status_code == 200
        data = response.json()
        assert data["source"] == "randomuser.me"

    @patch('src.routers.external.fetch_random_user')
    def test_random_user_handles_error(self, mock_fetch, client):
        """Test random user endpoint handles external API errors."""
        import httpx
        mock_fetch.side_effect = httpx.HTTPError("Connection failed")
        
        response = client.get("/v1/external/random-user")
        
        assert response.status_code == 200  # Graceful degradation
        data = response.json()
        assert "message" in data
        assert "Error" in data["message"]


class TestBackgroundTaskEndpoint:
    """Tests for background task endpoint."""

    def test_background_task_starts(self, client):
        """Test starting a background task."""
        response = client.post(
            "/v1/external/background-task?data=test_data"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data
        assert "message" in data
        assert "started" in data["message"].lower()

    def test_background_task_with_different_data(self, client):
        """Test background task with different data values."""
        response = client.post(
            "/v1/external/background-task?data=another_value"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["task_id"]) == 36  # UUID format


class TestExternalSchemas:
    """Tests for external endpoint schemas."""

    def test_external_api_response_schema(self):
        """Test ExternalAPIResponse schema validation."""
        from src.routers.external import ExternalAPIResponse
        
        response = ExternalAPIResponse(
            source="test",
            data={"key": "value"},
            message="Test message"
        )
        
        assert response.source == "test"
        assert response.data == {"key": "value"}
        assert response.message == "Test message"

    def test_background_task_status_schema(self):
        """Test BackgroundTaskStatus schema validation."""
        from src.routers.external import BackgroundTaskStatus
        
        status = BackgroundTaskStatus(
            message="Task completed",
            task_id="abc-123"
        )
        
        assert status.message == "Task completed"
        assert status.task_id == "abc-123"


class TestFetchRandomUser:
    """Tests for the fetch_random_user async function."""

    @pytest.mark.asyncio
    async def test_fetch_random_user_function(self):
        """Test fetch_random_user function directly."""
        from src.routers.external import fetch_random_user
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = {"results": [{"name": "Test"}]}
            
            mock_instance = AsyncMock()
            mock_instance.get.return_value = mock_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance
            
            result = await fetch_random_user()
            
            assert result == {"results": [{"name": "Test"}]}
