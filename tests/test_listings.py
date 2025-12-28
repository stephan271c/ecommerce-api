"""
Tests for listing CRUD endpoints.
"""

import pytest


class TestCreateListing:
    """Tests for creating listings."""

    def test_create_listing_success(self, client, test_user, auth_header):
        """Test successful listing creation."""
        response = client.post(
            "/v1/listings",
            headers=auth_header,
            json={
                "title": "New Product",
                "description": "A great product",
                "price": 49.99,
                "quantity": 5,
                "category": "electronics"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "New Product"
        assert data["price"] == 49.99
        assert "id" in data
        assert "seller_id" in data

    def test_create_listing_unauthenticated(self, client):
        """Test creating listing without authentication."""
        response = client.post(
            "/v1/listings",
            json={
                "title": "New Product",
                "price": 49.99
            }
        )
        
        assert response.status_code == 401

    def test_create_listing_invalid_price(self, client, test_user, auth_header):
        """Test creating listing with invalid price."""
        response = client.post(
            "/v1/listings",
            headers=auth_header,
            json={
                "title": "Bad Product",
                "price": -10.00
            }
        )
        
        assert response.status_code == 422


class TestListListings:
    """Tests for listing listings (public endpoint)."""

    def test_list_listings_public(self, client, test_listing):
        """Test listing listings without authentication."""
        response = client.get("/v1/listings")
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    def test_list_listings_pagination(self, client, test_listing):
        """Test listing pagination."""
        response = client.get("/v1/listings?skip=0&limit=5")
        
        assert response.status_code == 200
        data = response.json()
        assert data["skip"] == 0
        assert data["limit"] == 5

    def test_list_listings_filter_category(self, client, test_listing):
        """Test filtering by category."""
        response = client.get(
            f"/v1/listings?category={test_listing.category}"
        )
        
        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["category"] == test_listing.category

    def test_list_listings_filter_price_range(self, client, test_listing):
        """Test filtering by price range."""
        response = client.get(
            "/v1/listings?min_price=50&max_price=150"
        )
        
        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert 50 <= item["price"] <= 150

    def test_list_listings_sort_by_price(self, client, test_listing):
        """Test sorting by price."""
        response = client.get(
            "/v1/listings?sort_by=price&sort_order=asc"
        )
        
        assert response.status_code == 200


class TestGetListing:
    """Tests for getting a single listing."""

    def test_get_listing_success(self, client, test_listing):
        """Test getting a listing by ID."""
        response = client.get(f"/v1/listings/{test_listing.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_listing.id
        assert data["title"] == test_listing.title

    def test_get_listing_not_found(self, client):
        """Test getting a non-existent listing."""
        response = client.get("/v1/listings/99999")
        
        assert response.status_code == 404


class TestUpdateListing:
    """Tests for updating listings."""

    def test_update_own_listing(self, client, test_user, test_listing, auth_header):
        """Test updating own listing."""
        response = client.put(
            f"/v1/listings/{test_listing.id}",
            headers=auth_header,
            json={"title": "Updated Title", "price": 79.99}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["price"] == 79.99

    def test_admin_update_any_listing(
        self, client, test_user, admin_user, test_listing, admin_auth_header
    ):
        """Test that admin can update any listing."""
        response = client.put(
            f"/v1/listings/{test_listing.id}",
            headers=admin_auth_header,
            json={"title": "Admin Updated"}
        )
        
        assert response.status_code == 200


class TestDeleteListing:
    """Tests from src.models.models import Listings."""

    def test_delete_own_listing(self, client, test_user, test_listing, auth_header):
        """Test deleting own listing."""
        response = client.delete(
            f"/v1/listings/{test_listing.id}",
            headers=auth_header
        )
        
        assert response.status_code == 200
        assert "deleted" in response.json()["message"].lower()

    def test_delete_listing_not_found(self, client, test_user, auth_header):
        """Test deleting non-existent listing."""
        response = client.delete(
            "/v1/listings/99999",
            headers=auth_header
        )
        
        assert response.status_code == 404
