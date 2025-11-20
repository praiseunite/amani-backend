"""Tests for bot link API endpoint."""

import hmac
import hashlib
from datetime import datetime

from app.domain.entities import WalletProvider


def generate_hmac_signature(method: str, path: str, timestamp: str, body: str, secret: str) -> str:
    """Generate HMAC signature for request.

    Args:
        method: HTTP method
        path: Request path
        timestamp: Request timestamp
        body: Request body
        secret: API key secret

    Returns:
        HMAC signature
    """
    message = f"{method}{path}{timestamp}{body}"
    return hmac.new(secret.encode("utf-8"), message.encode("utf-8"), hashlib.sha256).hexdigest()


class TestBotLinkAPI:
    """Test cases for bot link endpoint."""

    def test_bot_link_success(self, client, test_user, api_key, components):
        """Test successful bot linking with HMAC auth."""
        # First create a link token
        create_response = client.post(
            "/api/v1/link_tokens/create",
            json={
                "user_id": str(test_user.id),
                "provider": WalletProvider.FINCRA.value,
            },
        )
        assert create_response.status_code == 201
        token = create_response.json()["token"]

        # Now link the bot using HMAC auth
        timestamp = str(int(datetime.utcnow().timestamp()))
        body = (
            f'{{"token":"{token}","provider_account_id":"acc123","provider_customer_id":"cust456"}}'
        )
        signature = generate_hmac_signature(
            "POST", "/api/v1/bot/link", timestamp, body, api_key["secret"]
        )

        response = client.post(
            "/api/v1/bot/link",
            content=body,
            headers={
                "Content-Type": "application/json",
                "X-API-KEY-ID": api_key["key_id"],
                "X-API-TIMESTAMP": timestamp,
                "X-API-SIGNATURE": signature,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "wallet_id" in data
        assert data["user_id"] == str(test_user.id)

        # Verify audit event was recorded
        audit_events = components["audit_port"].get_events()
        link_events = [e for e in audit_events if e["action"] == "link_wallet"]
        assert len(link_events) == 1

    def test_bot_link_missing_hmac_headers(self, client):
        """Test bot link without HMAC headers."""
        response = client.post(
            "/api/v1/bot/link",
            json={
                "token": "some-token",
                "provider_account_id": "acc123",
            },
        )

        assert response.status_code == 401
        assert "Missing required HMAC headers" in response.json()["detail"]

    def test_bot_link_invalid_signature(self, client, api_key):
        """Test bot link with invalid HMAC signature."""
        timestamp = str(int(datetime.utcnow().timestamp()))
        body = '{"token":"some-token","provider_account_id":"acc123"}'

        response = client.post(
            "/api/v1/bot/link",
            content=body,
            headers={
                "Content-Type": "application/json",
                "X-API-KEY-ID": api_key["key_id"],
                "X-API-TIMESTAMP": timestamp,
                "X-API-SIGNATURE": "invalid-signature",
            },
        )

        assert response.status_code == 401
        assert "Invalid HMAC signature" in response.json()["detail"]

    def test_bot_link_expired_timestamp(self, client, api_key):
        """Test bot link with expired timestamp."""
        # Use a timestamp from 10 minutes ago (outside the 5-minute window)
        timestamp = str(int(datetime.utcnow().timestamp()) - 600)
        body = '{"token":"some-token","provider_account_id":"acc123"}'
        signature = generate_hmac_signature(
            "POST", "/api/v1/bot/link", timestamp, body, api_key["secret"]
        )

        response = client.post(
            "/api/v1/bot/link",
            content=body,
            headers={
                "Content-Type": "application/json",
                "X-API-KEY-ID": api_key["key_id"],
                "X-API-TIMESTAMP": timestamp,
                "X-API-SIGNATURE": signature,
            },
        )

        assert response.status_code == 401
        assert "outside valid time window" in response.json()["detail"]

    def test_bot_link_invalid_token(self, client, api_key):
        """Test bot link with invalid link token."""
        timestamp = str(int(datetime.utcnow().timestamp()))
        body = '{"token":"invalid-token","provider_account_id":"acc123"}'
        signature = generate_hmac_signature(
            "POST", "/api/v1/bot/link", timestamp, body, api_key["secret"]
        )

        response = client.post(
            "/api/v1/bot/link",
            content=body,
            headers={
                "Content-Type": "application/json",
                "X-API-KEY-ID": api_key["key_id"],
                "X-API-TIMESTAMP": timestamp,
                "X-API-SIGNATURE": signature,
            },
        )

        assert response.status_code == 400
        assert "Invalid, expired, or already consumed" in response.json()["detail"]

    def test_bot_link_already_consumed_token(self, client, test_user, api_key, components):
        """Test bot link with already consumed token."""
        # Create and consume a token
        create_response = client.post(
            "/api/v1/link_tokens/create",
            json={
                "user_id": str(test_user.id),
                "provider": WalletProvider.FINCRA.value,
            },
        )
        token = create_response.json()["token"]

        # First consumption
        timestamp = str(int(datetime.utcnow().timestamp()))
        body = f'{{"token":"{token}","provider_account_id":"acc123"}}'
        signature = generate_hmac_signature(
            "POST", "/api/v1/bot/link", timestamp, body, api_key["secret"]
        )

        response1 = client.post(
            "/api/v1/bot/link",
            content=body,
            headers={
                "Content-Type": "application/json",
                "X-API-KEY-ID": api_key["key_id"],
                "X-API-TIMESTAMP": timestamp,
                "X-API-SIGNATURE": signature,
            },
        )
        assert response1.status_code == 200

        # Second consumption (should fail)
        timestamp2 = str(int(datetime.utcnow().timestamp()))
        signature2 = generate_hmac_signature(
            "POST", "/api/v1/bot/link", timestamp2, body, api_key["secret"]
        )

        response2 = client.post(
            "/api/v1/bot/link",
            content=body,
            headers={
                "Content-Type": "application/json",
                "X-API-KEY-ID": api_key["key_id"],
                "X-API-TIMESTAMP": timestamp2,
                "X-API-SIGNATURE": signature2,
            },
        )
        assert response2.status_code == 400
