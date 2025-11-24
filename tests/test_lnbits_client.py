"""
Unit tests for LNbits client.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.lnbits import LNbitsClient, LNbitsError


class TestLNbitsClient:
    """Test suite for LNbits API client."""

    def test_client_initialization(self):
        """Test that LNbits client initializes correctly with credentials."""
        client = LNbitsClient(
            api_key="test-api-key",
            base_url="https://test.lnbits.com",
            max_retries=3,
        )

        assert client.api_key == "test-api-key"
        assert client.base_url == "https://test.lnbits.com"
        assert client.max_retries == 3

    def test_client_with_custom_retries(self):
        """Test client with custom retry configuration."""
        client = LNbitsClient(
            api_key="test-key",
            max_retries=5,
            retry_delay=2.0,
            timeout=60.0,
        )

        assert client.max_retries == 5
        assert client.retry_delay == 2.0
        assert client.timeout == 60.0

    def test_lnbits_error_creation(self):
        """Test LNbitsError exception creation."""
        error = LNbitsError(
            message="Test error",
            status_code=400,
            response_data={"detail": "Bad request"},
        )

        assert error.message == "Test error"
        assert error.status_code == 400
        assert error.response_data == {"detail": "Bad request"}
        assert str(error) == "Test error"

    @pytest.mark.asyncio
    async def test_create_wallet_success(self):
        """Test successful wallet creation."""
        client = LNbitsClient(api_key="test-key")

        with patch.object(client, "_make_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {
                "id": "wallet123",
                "name": "test_wallet",
                "user": "testuser",
                "adminkey": "admin123",
                "inkey": "invoice123",
            }

            result = await client.create_wallet(
                user_name="testuser",
                wallet_name="test_wallet",
            )

            assert result["id"] == "wallet123"
            assert result["name"] == "test_wallet"
            assert result["adminkey"] == "admin123"
            mock_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_invoice_success(self):
        """Test successful invoice creation."""
        client = LNbitsClient(api_key="test-key")

        with patch.object(client, "_make_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {
                "payment_hash": "hash123",
                "payment_request": "lnbc1000n...",
                "checking_id": "check123",
            }

            result = await client.create_invoice(
                amount=1000,
                memo="Test payment",
                unit="sat",
            )

            assert result["payment_hash"] == "hash123"
            assert result["payment_request"] == "lnbc1000n..."
            mock_request.assert_called_once_with(
                "POST",
                "/api/v1/payments",
                data={
                    "amount": 1000,
                    "memo": "Test payment",
                    "unit": "sat",
                    "out": False,
                },
            )

    @pytest.mark.asyncio
    async def test_check_invoice_status(self):
        """Test checking invoice status."""
        client = LNbitsClient(api_key="test-key")

        with patch.object(client, "_make_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {
                "checking_id": "check123",
                "pending": False,
                "amount": 1000,
                "payment_hash": "hash123",
            }

            result = await client.check_invoice("hash123")

            assert result["payment_hash"] == "hash123"
            assert result["pending"] is False
            mock_request.assert_called_once_with("GET", "/api/v1/payments/hash123")

    @pytest.mark.asyncio
    async def test_decode_invoice(self):
        """Test decoding a Lightning invoice."""
        client = LNbitsClient(api_key="test-key")

        with patch.object(client, "_make_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {
                "payment_hash": "hash123",
                "amount_msat": 1000000,
                "description": "Test payment",
                "date": 1234567890,
                "expiry": 3600,
            }

            result = await client.decode_invoice("lnbc1000n...")

            assert result["payment_hash"] == "hash123"
            assert result["amount_msat"] == 1000000
            mock_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_balance(self):
        """Test getting wallet balance."""
        client = LNbitsClient(api_key="test-key")

        with patch.object(client, "get_wallet_details", new_callable=AsyncMock) as mock_details:
            mock_details.return_value = {
                "id": "wallet123",
                "name": "test_wallet",
                "balance": 5000000,
            }

            result = await client.get_balance()

            assert result["balance"] == 5000000
            assert result["currency"] == "msat"
            mock_details.assert_called_once()

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling in API requests."""
        client = LNbitsClient(api_key="test-key")

        with patch.object(client, "_make_request", new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = LNbitsError(
                message="API error",
                status_code=400,
            )

            with pytest.raises(LNbitsError) as exc_info:
                await client.create_wallet("testuser")

            assert exc_info.value.status_code == 400
            assert "API error" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test async context manager usage."""
        async with LNbitsClient(api_key="test-key") as client:
            assert client.api_key == "test-key"
            assert client.client is not None
