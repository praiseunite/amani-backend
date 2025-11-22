"""Tests for user status endpoint."""

import hashlib
import hmac
from datetime import datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.app import create_app
from app.composition import build_app_components
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


@pytest.fixture
def api_key_repo(components):
    """Get API key repository."""
    return components["api_key_port"]


def create_hmac_signature(key_id: str, secret: str, timestamp: int) -> str:
    """Create HMAC signature for testing."""
    message = f"{key_id}:{timestamp}".encode("utf-8")
    signature = hmac.new(
        secret.encode("utf-8"),
        message,
        hashlib.sha256,
    ).hexdigest()
    return signature


class TestUsersStatus:
    """Test suite for user status endpoint."""

    @pytest.mark.asyncio
    async def test_get_user_status_success(self, client, user_repository):
        """Test getting user status successfully with X-USER-ID."""
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

        # Make request with X-USER-ID header
        response = client.get(
            f"/api/v1/users/{user.id}/status",
            headers={"X-USER-ID": str(user.id)},
        )

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
    async def test_get_user_status_success_hmac(self, client, user_repository, api_key_repo):
        """Test getting user status successfully with HMAC."""
        # Setup: Create a user
        user = User(
            id=uuid4(),
            email="hmac@example.com",
            full_name="HMAC User",
            role="client",
            is_active=True,
        )
        await user_repository.save(user)

        # Setup: Add API key
        key_id = "test-key"
        secret = "test-secret"
        api_key_repo.add_key(key_id, secret)

        # Create HMAC headers
        timestamp = int(datetime.utcnow().timestamp())
        signature = create_hmac_signature(key_id, secret, timestamp)

        # Make request
        response = client.get(
            f"/api/v1/users/{user.id}/status",
            headers={
                "X-API-KEY-ID": key_id,
                "X-API-TIMESTAMP": str(timestamp),
                "X-API-SIGNATURE": signature,
            },
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == str(user.id)

    @pytest.mark.asyncio
    async def test_get_user_status_not_found(self, client):
        """Test getting status for non-existent user."""
        # Make request with random UUID and correct user ID header
        user_id = uuid4()
        response = client.get(
            f"/api/v1/users/{user_id}/status",
            headers={"X-USER-ID": str(user_id)},
        )

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
    async def test_get_user_status_missing_auth(self, client):
        """Test getting status without authentication."""
        user_id = uuid4()
        response = client.get(f"/api/v1/users/{user_id}/status")

        # Assert
        assert response.status_code == 401
        assert "Missing authentication headers" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_user_status_forbidden(self, client, user_repository):
        """Test getting status for another user (forbidden)."""
        # Setup: Create a user
        user = User(id=uuid4())
        await user_repository.save(user)

        # Make request with different X-USER-ID
        other_user_id = uuid4()
        response = client.get(
            f"/api/v1/users/{user.id}/status",
            headers={"X-USER-ID": str(other_user_id)},
        )

        # Assert
        assert response.status_code == 403
        assert "Not authorized" in response.json()["detail"]
