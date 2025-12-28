"""
Tests for user CRUD endpoints.
"""

import pytest


class TestListUsers:
    """Tests for listing users."""

    def test_list_users_authenticated(self, client, test_user, auth_header):
        """Test listing users with authentication."""
        response = client.get("/v1/users", headers=auth_header)
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] >= 1

    def test_list_users_unauthenticated(self, client):
        """Test listing users without authentication."""
        response = client.get("/v1/users")
        
        assert response.status_code == 401

    def test_list_users_pagination(self, client, test_user, auth_header):
        """Test user list pagination."""
        response = client.get(
            "/v1/users?skip=0&limit=5",
            headers=auth_header
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["skip"] == 0
        assert data["limit"] == 5


class TestGetUser:
    """Tests for getting a single user."""

    def test_get_user_success(self, client, test_user, auth_header):
        """Test getting a user by ID."""
        response = client.get(
            f"/v1/users/{test_user.id}",
            headers=auth_header
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_user.id
        assert data["email"] == test_user.email

    def test_get_user_not_found(self, client, test_user, auth_header):
        """Test getting a non-existent user."""
        response = client.get(
            "/v1/users/99999",
            headers=auth_header
        )
        
        assert response.status_code == 404

    def test_get_current_user(self, client, test_user, auth_header):
        """Test getting current user profile."""
        response = client.get("/v1/users/me", headers=auth_header)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_user.id


class TestUpdateUser:
    """Tests for updating users."""

    def test_update_own_profile(self, client, test_user, auth_header):
        """Test updating own profile."""
        response = client.put(
            f"/v1/users/{test_user.id}",
            headers=auth_header,
            json={"username": "updatedname"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "updatedname"

    def test_update_other_user_forbidden(self, client, test_user, admin_user, auth_header):
        """Test updating another user's profile (forbidden)."""
        response = client.put(
            f"/v1/users/{admin_user.id}",
            headers=auth_header,
            json={"username": "hackername"}
        )
        
        assert response.status_code == 403

    def test_admin_update_any_user(self, client, test_user, admin_user, admin_auth_header):
        """Test admin can update any user."""
        response = client.put(
            f"/v1/users/{test_user.id}",
            headers=admin_auth_header,
            json={"username": "adminupdated"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "adminupdated"


class TestDeleteUser:
    """Tests for deleting users."""

    def test_delete_own_account(self, client, test_user, auth_header):
        """Test deleting own account."""
        response = client.delete(
            f"/v1/users/{test_user.id}",
            headers=auth_header
        )
        
        assert response.status_code == 200
        assert "deleted" in response.json()["message"].lower()

    def test_delete_other_user_forbidden(self, client, test_user, admin_user, auth_header):
        """Test deleting another user (forbidden)."""
        response = client.delete(
            f"/v1/users/{admin_user.id}",
            headers=auth_header
        )
        
        assert response.status_code == 403
