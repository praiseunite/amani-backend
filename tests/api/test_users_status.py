"""Tests for user status endpoint."""

import pytest
from uuid import uuid4
from fastapi.testclient import TestClient

from app.composition import build_app_components
from app.api.app import create_app
from app.domain.entities import User


@pytest.fixture
def components():
    """Build application components."""
    return build_app_components()


@pytest.fixture
def client(components):
    """Create test client."""
    app = create_app(components)
    return TestClient(app)


@pytest.fixture
def user_repository(components):
    """Get user repository."""
    return components["user_repository_port"]


class TestUsersStatus:
    """Test suite for user status endpoint."""

    @pytest.mark.asyncio
    async def test_get_user_status_success(self, client, user_repository):
        """Test getting user status successfully."""
        # Setup: Create a user
        user = User(
            id=uuid4(),
            email="test@example.com",
            full_name="Test User",
            role="client",
            is_active=True,
            is_verified=False,
        )
        await user_repository.save(user)

        # Make request
        response = client.get(f"/api/v1/users/{user.id}/status")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == str(user.id)
        assert data["email"] == "test@example.com"
        assert data["full_name"] == "Test User"
        assert data["role"] == "client"
        assert data["is_active"] is True
        assert data["is_verified"] is False

    @pytest.mark.asyncio
    async def test_get_user_status_not_found(self, client):
        """Test getting status for non-existent user."""
        # Make request with random UUID
        user_id = uuid4()
        response = client.get(f"/api/v1/users/{user_id}/status")

        # Assert
        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_user_status_invalid_uuid(self, client):
        """Test getting status with invalid UUID."""
        # Make request with invalid UUID
        response = client.get("/api/v1/users/invalid-uuid/status")

        # Assert validation error
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_user_status_verified_user(self, client, user_repository):
        """Test getting status for a verified user."""
        # Setup: Create a verified user
        user = User(
            id=uuid4(),
            email="verified@example.com",
            full_name="Verified User",
            role="freelancer",
            is_active=True,
            is_verified=True,
        )
        await user_repository.save(user)

        # Make request
        response = client.get(f"/api/v1/users/{user.id}/status")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["is_verified"] is True
        assert data["role"] == "freelancer"
