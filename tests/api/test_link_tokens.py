"""Tests for link tokens API endpoint."""

from app.domain.entities import WalletProvider


class TestLinkTokensAPI:
    """Test cases for link tokens endpoint."""

    def test_create_link_token_success(self, client, test_user):
        """Test successful link token creation."""
        response = client.post(
            "/api/v1/link_tokens/create",
            json={
                "user_id": str(test_user.id),
                "provider": WalletProvider.FINCRA.value,
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert "token" in data
        assert "expires_at" in data
        assert data["provider"] == WalletProvider.FINCRA.value
        assert len(data["token"]) > 0

    def test_create_link_token_different_providers(self, client, test_user):
        """Test creating link tokens for different providers."""
        providers = [WalletProvider.FINCRA, WalletProvider.PAYSTACK, WalletProvider.FLUTTERWAVE]

        for provider in providers:
            response = client.post(
                "/api/v1/link_tokens/create",
                json={
                    "user_id": str(test_user.id),
                    "provider": provider.value,
                },
            )

            assert response.status_code == 201
            data = response.json()
            assert data["provider"] == provider.value

    def test_create_link_token_invalid_provider(self, client, test_user):
        """Test creating link token with invalid provider."""
        response = client.post(
            "/api/v1/link_tokens/create",
            json={
                "user_id": str(test_user.id),
                "provider": "invalid_provider",
            },
        )

        assert response.status_code == 422  # Validation error

    def test_create_link_token_invalid_user_id(self, client):
        """Test creating link token with invalid user ID format."""
        response = client.post(
            "/api/v1/link_tokens/create",
            json={
                "user_id": "not-a-uuid",
                "provider": WalletProvider.FINCRA.value,
            },
        )

        assert response.status_code == 422  # Validation error
