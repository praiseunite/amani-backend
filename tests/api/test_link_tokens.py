"""Tests for link tokens endpoint."""

import pytest
from uuid import uuid4
from fastapi.testclient import TestClient

from app.composition import build_app_components
from app.api.app import create_app


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
def audit_port(components):
    """Get audit port."""
    return components["audit_port"]


class TestLinkTokens:
    """Test suite for link tokens endpoint."""

    @pytest.mark.asyncio
    async def test_create_link_token_success(self, client, audit_port):
        """Test creating a link token successfully."""
        # Make request
        user_id = uuid4()
        response = client.post(
            "/api/v1/link_tokens/create",
            json={
                "user_id": str(user_id),
                "provider": "fincra",
            },
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert len(data["token"]) > 0
        assert "expires_at" in data
        assert data["provider"] == "fincra"

        # Verify audit event
        events = audit_port.get_events()
        assert len(events) == 1
        assert events[0]["action"] == "create_link_token"
        assert events[0]["user_id"] == user_id

    @pytest.mark.asyncio
    async def test_create_link_token_paystack(self, client):
        """Test creating a link token for Paystack provider."""
        # Make request
        user_id = uuid4()
        response = client.post(
            "/api/v1/link_tokens/create",
            json={
                "user_id": str(user_id),
                "provider": "paystack",
            },
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["provider"] == "paystack"

    @pytest.mark.asyncio
    async def test_create_link_token_flutterwave(self, client):
        """Test creating a link token for Flutterwave provider."""
        # Make request
        user_id = uuid4()
        response = client.post(
            "/api/v1/link_tokens/create",
            json={
                "user_id": str(user_id),
                "provider": "flutterwave",
            },
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["provider"] == "flutterwave"

    @pytest.mark.asyncio
    async def test_create_link_token_invalid_provider(self, client):
        """Test creating a link token with invalid provider."""
        # Make request
        response = client.post(
            "/api/v1/link_tokens/create",
            json={
                "user_id": str(uuid4()),
                "provider": "invalid-provider",
            },
        )

        # Assert validation error
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_link_token_invalid_user_id(self, client):
        """Test creating a link token with invalid user ID."""
        # Make request
        response = client.post(
            "/api/v1/link_tokens/create",
            json={
                "user_id": "invalid-uuid",
                "provider": "fincra",
            },
        )

        # Assert validation error
        assert response.status_code == 422
