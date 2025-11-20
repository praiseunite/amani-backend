"""Tests for link tokens endpoint."""

import pytest
from uuid import uuid4
from fastapi.testclient import TestClient

from app.composition import build_app_components
from app.api.app import create_app
from app.domain.entities import WalletProvider


@pytest.fixture
def components():
    """Build application components."""
    return build_app_components()


@pytest.fixture
def client(components):
    """Create test client."""
    app = create_app(components)
    return TestClient(app)


class TestLinkTokens:
    """Test suite for link tokens endpoint."""

    @pytest.mark.asyncio
    async def test_create_link_token_success(self, client):
        """Test creating a link token successfully."""
        user_id = uuid4()

        # Make request
        response = client.post(
            "/api/v1/link_tokens/create",
            json={
                "provider": "fincra",
            },
            headers={
                "X-USER-ID": str(user_id),
            },
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["token"] is not None
        assert data["expires_at"] is not None
        assert data["provider"] == "fincra"

    @pytest.mark.asyncio
    async def test_create_link_token_missing_auth(self, client):
        """Test creating link token without auth header."""
        # Make request
        response = client.post(
            "/api/v1/link_tokens/create",
            json={
                "provider": "fincra",
            },
        )

        # Assert
        assert response.status_code == 401
        assert "Missing X-USER-ID header" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_link_token_invalid_user_id(self, client):
        """Test creating link token with invalid user ID."""
        # Make request
        response = client.post(
            "/api/v1/link_tokens/create",
            json={
                "provider": "fincra",
            },
            headers={
                "X-USER-ID": "invalid-uuid",
            },
        )

        # Assert
        assert response.status_code == 401
        assert "Invalid user ID format" in response.json()["detail"]
