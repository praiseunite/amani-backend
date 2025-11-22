"""Tests for wallet registration endpoint."""

import hashlib
import hmac
from datetime import datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.app import create_app
from app.composition import build_app_components


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
def wallet_registry_port(components):
    """Get wallet registry port."""
    return components["wallet_registry_port"]


@pytest.fixture
def audit_port(components):
    """Get audit port."""
    return components["audit_port"]


def create_hmac_signature(key_id: str, secret: str, timestamp: int) -> str:
    """Create HMAC signature for testing."""
    message = f"{key_id}:{timestamp}".encode("utf-8")
    signature = hmac.new(
        secret.encode("utf-8"),
        message,
        hashlib.sha256,
    ).hexdigest()
    return signature


class TestWalletsRegister:
    """Test suite for wallet registration endpoint."""

    @pytest.mark.asyncio
    async def test_register_wallet_success(
        self, client, api_key_repo, wallet_registry_port, audit_port
    ):
        """Test successful wallet registration."""
        # Setup: Add API key
        key_id = "test-bot-key"
        secret = "test-secret"
        api_key_repo.add_key(key_id, secret)

        # Create HMAC headers
        timestamp = int(datetime.utcnow().timestamp())
        signature = create_hmac_signature(key_id, secret, timestamp)

        # Make request
        user_id = uuid4()
        response = client.post(
            "/api/v1/wallets/register",
            json={
                "user_id": str(user_id),
                "provider": "fincra",
                "provider_account_id": "fincra-account-123",
                "provider_customer_id": "customer-456",
                "metadata": {"source": "bot"},
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
        assert data["user_id"] == str(user_id)
        assert data["provider"] == "fincra"
        assert data["provider_account_id"] == "fincra-account-123"
        assert data["is_active"] is True

        # Verify audit events
        events = audit_port.get_events()
        assert len(events) == 1
        assert events[0]["action"] == "register_wallet"

    @pytest.mark.asyncio
    async def test_register_wallet_idempotent(self, client, api_key_repo, wallet_registry_port):
        """Test wallet registration is idempotent."""
        # Setup: Add API key
        key_id = "test-bot-key"
        secret = "test-secret"
        api_key_repo.add_key(key_id, secret)

        # Create HMAC headers
        timestamp = int(datetime.utcnow().timestamp())
        signature = create_hmac_signature(key_id, secret, timestamp)

        user_id = uuid4()
        request_data = {
            "user_id": str(user_id),
            "provider": "fincra",
            "provider_account_id": "fincra-account-123",
        }

        headers = {
            "X-API-KEY-ID": key_id,
            "X-API-TIMESTAMP": str(timestamp),
            "X-API-SIGNATURE": signature,
        }

        # Make first request
        response1 = client.post(
            "/api/v1/wallets/register",
            json=request_data,
            headers=headers,
        )

        # Update timestamp and signature for second request
        timestamp2 = int(datetime.utcnow().timestamp())
        signature2 = create_hmac_signature(key_id, secret, timestamp2)
        headers2 = {
            "X-API-KEY-ID": key_id,
            "X-API-TIMESTAMP": str(timestamp2),
            "X-API-SIGNATURE": signature2,
        }

        # Make second request with same data
        response2 = client.post(
            "/api/v1/wallets/register",
            json=request_data,
            headers=headers2,
        )

        # Assert both succeed
        assert response1.status_code == 200
        assert response2.status_code == 200

        # Assert same wallet is returned
        data1 = response1.json()
        data2 = response2.json()
        assert data1["wallet_id"] == data2["wallet_id"]
        assert data1["user_id"] == data2["user_id"]
        assert data1["provider"] == data2["provider"]

    @pytest.mark.asyncio
    async def test_register_wallet_missing_hmac_headers(self, client):
        """Test wallet registration without HMAC headers."""
        response = client.post(
            "/api/v1/wallets/register",
            json={
                "user_id": str(uuid4()),
                "provider": "fincra",
                "provider_account_id": "fincra-account-123",
            },
        )

        # Assert
        assert response.status_code == 401
        assert "Missing HMAC authentication headers" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_register_wallet_invalid_provider(self, client, api_key_repo):
        """Test wallet registration with invalid provider."""
        # Setup: Add API key
        key_id = "test-bot-key"
        secret = "test-secret"
        api_key_repo.add_key(key_id, secret)

        # Create HMAC headers
        timestamp = int(datetime.utcnow().timestamp())
        signature = create_hmac_signature(key_id, secret, timestamp)

        # Make request with invalid provider
        response = client.post(
            "/api/v1/wallets/register",
            json={
                "user_id": str(uuid4()),
                "provider": "invalid-provider",
                "provider_account_id": "account-123",
            },
            headers={
                "X-API-KEY-ID": key_id,
                "X-API-TIMESTAMP": str(timestamp),
                "X-API-SIGNATURE": signature,
            },
        )

        # Assert validation error
        assert response.status_code == 422
