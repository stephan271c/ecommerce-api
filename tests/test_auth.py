"""
Tests for authentication endpoints.
"""

import pytest


class TestRegister:
    """Tests for user registration."""

    def test_register_success(self, client):
        """Test successful user registration."""
        response = client.post(
            "/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "username": "newuser",
                "password": "NewPass123"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["username"] == "newuser"
        assert "id" in data
        assert "hashed_password" not in data

    def test_register_duplicate_email(self, client, test_user):
        """Test registration with existing email."""
        response = client.post(
            "/v1/auth/register",
            json={
                "email": test_user.email,
                "username": "differentuser",
                "password": "NewPass123"
            }
        )
        
        assert response.status_code == 409
        assert "already registered" in response.json()["message"]

    def test_register_duplicate_username(self, client, test_user):
        """Test registration with existing username."""
        response = client.post(
            "/v1/auth/register",
            json={
                "email": "different@example.com",
                "username": test_user.username,
                "password": "NewPass123"
            }
        )
        
        assert response.status_code == 409
        assert "already taken" in response.json()["message"]

    def test_register_weak_password(self, client):
        """Test registration with weak password."""
        response = client.post(
            "/v1/auth/register",
            json={
                "email": "weak@example.com",
                "username": "weakuser",
                "password": "weak"
            }
        )
        
        assert response.status_code == 422  # Validation error

    def test_register_invalid_email(self, client):
        """Test registration with invalid email."""
        response = client.post(
            "/v1/auth/register",
            json={
                "email": "invalid-email",
                "username": "validuser",
                "password": "ValidPass123"
            }
        )
        
        assert response.status_code == 422


class TestLogin:
    """Tests for user login."""

    def test_login_success(self, client, test_user):
        """Test successful login."""
        response = client.post(
            "/v1/auth/login",
            data={
                "username": "testuser",
                "password": "Test1234"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client, test_user):
        """Test login with wrong password."""
        response = client.post(
            "/v1/auth/login",
            data={
                "username": "testuser",
                "password": "WrongPassword"
            }
        )
        
        assert response.status_code == 401
        assert "Invalid" in response.json()["message"]

    def test_login_nonexistent_user(self, client):
        """Test login with non-existent user."""
        response = client.post(
            "/v1/auth/login",
            data={
                "username": "nonexistent",
                "password": "AnyPassword123"
            }
        )
        
        assert response.status_code == 401
