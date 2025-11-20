"""Tests for wallets registration API endpoint."""

import hmac
import hashlib
from datetime import datetime

from app.domain.entities import WalletProvider


def generate_hmac_signature(method: str, path: str, timestamp: str, body: str, secret: str) -> str:
    """Generate HMAC signature for request."""
    message = f"{method}{path}{timestamp}{body}"
    return hmac.new(secret.encode("utf-8"), message.encode("utf-8"), hashlib.sha256).hexdigest()


class TestWalletsRegisterAPI:
    """Test cases for wallet registration endpoint."""

    def test_register_wallet_success(self, client, test_user, api_key):
        """Test successful wallet registration with HMAC auth."""
        timestamp = str(int(datetime.utcnow().timestamp()))
        body = (
            f'{{"user_id":"{str(test_user.id)}","provider":"fincra",'
            f'"provider_account_id":"acc123","provider_customer_id":"cust456"}}'
        )
        signature = generate_hmac_signature(
            "POST", "/api/v1/wallets/register", timestamp, body, api_key["secret"]
        )

        response = client.post(
            "/api/v1/wallets/register",
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
        assert "wallet_id" in data
        assert data["user_id"] == str(test_user.id)
        assert data["provider"] == WalletProvider.FINCRA.value
        assert data["is_active"] is True

    def test_register_wallet_idempotent(self, client, test_user, api_key):
        """Test wallet registration is idempotent."""
        timestamp1 = str(int(datetime.utcnow().timestamp()))
        body = (
            f'{{"user_id":"{str(test_user.id)}","provider":"fincra",'
            f'"provider_account_id":"acc123"}}'
        )
        signature1 = generate_hmac_signature(
            "POST", "/api/v1/wallets/register", timestamp1, body, api_key["secret"]
        )

        # First registration
        response1 = client.post(
            "/api/v1/wallets/register",
            content=body,
            headers={
                "Content-Type": "application/json",
                "X-API-KEY-ID": api_key["key_id"],
                "X-API-TIMESTAMP": timestamp1,
                "X-API-SIGNATURE": signature1,
            },
        )

        assert response1.status_code == 200
        wallet_id_1 = response1.json()["wallet_id"]

        # Second registration with same parameters (should return existing wallet)
        timestamp2 = str(int(datetime.utcnow().timestamp()))
        signature2 = generate_hmac_signature(
            "POST", "/api/v1/wallets/register", timestamp2, body, api_key["secret"]
        )

        response2 = client.post(
            "/api/v1/wallets/register",
            content=body,
            headers={
                "Content-Type": "application/json",
                "X-API-KEY-ID": api_key["key_id"],
                "X-API-TIMESTAMP": timestamp2,
                "X-API-SIGNATURE": signature2,
            },
        )

        assert response2.status_code == 200
        wallet_id_2 = response2.json()["wallet_id"]

        # Should return the same wallet ID (idempotent)
        assert wallet_id_1 == wallet_id_2

    def test_register_wallet_different_providers(self, client, test_user, api_key):
        """Test registering wallets for different providers."""
        providers = [WalletProvider.FINCRA, WalletProvider.PAYSTACK, WalletProvider.FLUTTERWAVE]

        for provider in providers:
            timestamp = str(int(datetime.utcnow().timestamp()))
            body = (
                f'{{"user_id":"{str(test_user.id)}","provider":"{provider.value}",'
                f'"provider_account_id":"acc-{provider.value}"}}'
            )
            signature = generate_hmac_signature(
                "POST", "/api/v1/wallets/register", timestamp, body, api_key["secret"]
            )

            response = client.post(
                "/api/v1/wallets/register",
                content=body,
                headers={
                    "Content-Type": "application/json",
                    "X-API-KEY-ID": api_key["key_id"],
                    "X-API-TIMESTAMP": timestamp,
                    "X-API-SIGNATURE": signature,
                },
            )

            assert response.status_code == 200
            assert response.json()["provider"] == provider.value

    def test_register_wallet_missing_hmac_headers(self, client, test_user):
        """Test wallet registration without HMAC headers."""
        response = client.post(
            "/api/v1/wallets/register",
            json={
                "user_id": str(test_user.id),
                "provider": WalletProvider.FINCRA.value,
                "provider_account_id": "acc123",
            },
        )

        assert response.status_code == 401
        assert "Missing required HMAC headers" in response.json()["detail"]

    def test_register_wallet_invalid_signature(self, client, test_user, api_key):
        """Test wallet registration with invalid HMAC signature."""
        timestamp = str(int(datetime.utcnow().timestamp()))
        body = (
            f'{{"user_id":"{str(test_user.id)}","provider":"fincra",'
            f'"provider_account_id":"acc123"}}'
        )

        response = client.post(
            "/api/v1/wallets/register",
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

    def test_register_wallet_audit_logging(self, client, test_user, api_key, components):
        """Test that wallet registration is audited."""
        timestamp = str(int(datetime.utcnow().timestamp()))
        body = (
            f'{{"user_id":"{str(test_user.id)}","provider":"fincra",'
            f'"provider_account_id":"acc123"}}'
        )
        signature = generate_hmac_signature(
            "POST", "/api/v1/wallets/register", timestamp, body, api_key["secret"]
        )

        response = client.post(
            "/api/v1/wallets/register",
            content=body,
            headers={
                "Content-Type": "application/json",
                "X-API-KEY-ID": api_key["key_id"],
                "X-API-TIMESTAMP": timestamp,
                "X-API-SIGNATURE": signature,
            },
        )

        assert response.status_code == 200

        # Verify audit event was recorded
        audit_events = components["audit_port"].get_events()
        register_events = [e for e in audit_events if e["action"] == "register_wallet"]
        assert len(register_events) == 1
        assert register_events[0]["user_id"] == test_user.id
