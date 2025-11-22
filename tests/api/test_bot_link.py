"""Tests for bot link endpoint."""

import pytest
import hmac
import hashlib
from datetime import datetime
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


@pytest.fixture
def api_key_repo(components):
    """Get API key repository."""
    return components["api_key_port"]


@pytest.fixture
def link_token_service(components):
    """Get link token service."""
    return components["link_token_service"]


@pytest.fixture
def audit_port(components):
    """Get audit port."""
    return components["audit_port"]


def create_hmac_signature(key_id: str, secret: str, timestamp: int) -> str:
    """Create HMAC signature for testing.

    Args:
        key_id: API key ID
        secret: API key secret
        timestamp: Request timestamp

    Returns:
        HMAC signature
    """
    message = f"{key_id}:{timestamp}".encode("utf-8")
    signature = hmac.new(
        secret.encode("utf-8"),
        message,
        hashlib.sha256,
    ).hexdigest()
    return signature


class TestBotLink:
    """Test suite for bot link endpoint."""

    @pytest.mark.asyncio
    async def test_bot_link_success(self, client, api_key_repo, link_token_service, audit_port):
        """Test successful bot linking."""
        # Setup: Add API key
        key_id = "test-bot-key"
        secret = "test-secret"
        api_key_repo.add_key(key_id, secret)

        # Setup: Create link token
        user_id = uuid4()
        provider = WalletProvider.FINCRA
        link_token = await link_token_service.create_link_token(user_id, provider)

        # Create HMAC headers
        timestamp = int(datetime.utcnow().timestamp())
        signature = create_hmac_signature(key_id, secret, timestamp)

        # Make request
        response = client.post(
            "/api/v1/bot/link",
            json={
                "token": link_token.token,
                "provider_account_id": "fincra-account-123",
            },
            headers={
                "X-API-KEY-ID": key_id,
                "X-API-TIMESTAMP": str(timestamp),
                "X-API-SIGNATURE": signature,
            },
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Bot linked successfully"

        # Verify audit events
        events = audit_port.get_events()
        assert len(events) == 2  # create and consume
        assert events[1]["action"] == "consume_link_token"

    @pytest.mark.asyncio
    async def test_bot_link_invalid_token(self, client, api_key_repo):
        """Test bot linking with invalid token."""
        # Setup: Add API key
        key_id = "test-bot-key"
        secret = "test-secret"
        api_key_repo.add_key(key_id, secret)

        # Create HMAC headers
        timestamp = int(datetime.utcnow().timestamp())
        signature = create_hmac_signature(key_id, secret, timestamp)

        # Make request with invalid token
        response = client.post(
            "/api/v1/bot/link",
            json={
                "token": "invalid-token",
                "provider_account_id": "fincra-account-123",
            },
            headers={
                "X-API-KEY-ID": key_id,
                "X-API-TIMESTAMP": str(timestamp),
                "X-API-SIGNATURE": signature,
            },
        )

        # Assert
        assert response.status_code == 400
        assert "Invalid or expired token" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_bot_link_missing_hmac_headers(self, client):
        """Test bot linking without HMAC headers."""
        response = client.post(
            "/api/v1/bot/link",
            json={
                "token": "some-token",
                "provider_account_id": "fincra-account-123",
            },
        )

        # Assert
        assert response.status_code == 401
        assert "Missing HMAC authentication headers" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_bot_link_invalid_signature(self, client, api_key_repo):
        """Test bot linking with invalid signature."""
        # Setup: Add API key
        key_id = "test-bot-key"
        secret = "test-secret"
        api_key_repo.add_key(key_id, secret)

        # Create HMAC headers with wrong signature
        timestamp = int(datetime.utcnow().timestamp())

        # Make request with invalid signature
        response = client.post(
            "/api/v1/bot/link",
            json={
                "token": "some-token",
                "provider_account_id": "fincra-account-123",
            },
            headers={
                "X-API-KEY-ID": key_id,
                "X-API-TIMESTAMP": str(timestamp),
                "X-API-SIGNATURE": "invalid-signature",
            },
        )

        # Assert
        assert response.status_code == 401
        assert "Invalid signature" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_bot_link_invalid_api_key(self, client):
        """Test bot linking with invalid API key."""
        # Create HMAC headers
        timestamp = int(datetime.utcnow().timestamp())
        signature = create_hmac_signature("invalid-key", "secret", timestamp)

        # Make request
        response = client.post(
            "/api/v1/bot/link",
            json={
                "token": "some-token",
                "provider_account_id": "fincra-account-123",
            },
            headers={
                "X-API-KEY-ID": "invalid-key",
                "X-API-TIMESTAMP": str(timestamp),
                "X-API-SIGNATURE": signature,
            },
        )

        # Assert
        assert response.status_code == 401
        assert "Invalid API key" in response.json()["detail"]
