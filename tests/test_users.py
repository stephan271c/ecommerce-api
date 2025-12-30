"""
Tests for user CRUD endpoints.
"""

import pytest


class TestListUsers:
    """Tests for listing users."""

    def test_list_users_regular_forbidden(self, client, test_user, auth_header):
        """Test listing users as regular user is forbidden."""
        response = client.get("/v1/users", headers=auth_header)
        
        assert response.status_code == 403

    def test_list_users_admin_success(self, client, admin_user, admin_auth_header):
        """Test listing users as admin is allowed."""
        response = client.get("/v1/users", headers=admin_auth_header)
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] >= 1

    def test_list_users_unauthenticated(self, client):
        """Test listing users without authentication."""
        response = client.get("/v1/users")
        
        assert response.status_code == 401

    def test_list_users_pagination(self, client, admin_user, admin_auth_header):
        """Test user list pagination (requires admin)."""
        response = client.get(
            "/v1/users?skip=0&limit=5",
            headers=admin_auth_header
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

    def test_get_other_user_forbidden(self, client, test_user, admin_user, auth_header):
        """Test getting another user's profile is forbidden."""
        response = client.get(
            f"/v1/users/{admin_user.id}",
            headers=auth_header
        )
        
        assert response.status_code == 403

    def test_admin_get_any_user(self, client, test_user, admin_user, admin_auth_header):
        """Test admin can get any user profile."""
        response = client.get(
            f"/v1/users/{test_user.id}",
            headers=admin_auth_header
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_user.id

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
    """Tests from src.models.models import Users."""

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


class TestUpdateUserRole:
    """Tests for updating user roles."""

    def test_update_role_admin_success(self, client, test_user, admin_user, admin_auth_header):
        """Test admin promoting a user."""
        response = client.put(
            f"/v1/users/{test_user.id}/role",
            headers=admin_auth_header,
            json={"role": "admin"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "admin"
        
        # Verify persistence
        # We need to query via DB to be sure, but TestClient interactions are committed
        # Re-fetching via API to confirm
        response_check = client.get(
            f"/v1/users/{test_user.id}",
            headers=admin_auth_header
        )
        assert response_check.json()["role"] == "admin"

    def test_update_role_regular_forbidden(self, client, test_user, admin_user, auth_header):
        """Test regular user cannot change roles."""
        response = client.put(
            f"/v1/users/{admin_user.id}/role",
            headers=auth_header,
            json={"role": "user"}
        )
        
        assert response.status_code == 403

    def test_update_role_invalid_value(self, client, test_user, admin_user, admin_auth_header):
        """Test validation of role values."""
        response = client.put(
            f"/v1/users/{test_user.id}/role",
            headers=admin_auth_header,
            json={"role": "supergod"}
        )
        
        assert response.status_code == 422
