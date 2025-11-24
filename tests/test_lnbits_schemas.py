"""
Unit tests for LNbits schemas.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from app.schemas.lnbits import (
    LNbitsBalanceResponse,
    LNbitsDecodeInvoiceRequest,
    LNbitsDecodeInvoiceResponse,
    LNbitsInternalTransferRequest,
    LNbitsInternalTransferResponse,
    LNbitsInvoiceCreateRequest,
    LNbitsInvoiceResponse,
    LNbitsPaymentRequest,
    LNbitsPaymentStatusRequest,
    LNbitsPaymentStatusResponse,
    LNbitsWalletCreateRequest,
    LNbitsWalletDetailsResponse,
    LNbitsWalletResponse,
)


class TestLNbitsSchemas:
    """Test suite for LNbits Pydantic schemas."""

    def test_wallet_create_request_valid(self):
        """Test valid wallet creation request."""
        data = {
            "user_name": "testuser",
            "wallet_name": "Test Wallet",
        }
        schema = LNbitsWalletCreateRequest(**data)
        assert schema.user_name == "testuser"
        assert schema.wallet_name == "Test Wallet"

    def test_wallet_create_request_minimal(self):
        """Test wallet creation request with minimal data."""
        data = {"user_name": "testuser"}
        schema = LNbitsWalletCreateRequest(**data)
        assert schema.user_name == "testuser"
        assert schema.wallet_name is None

    def test_wallet_response(self):
        """Test wallet response schema."""
        data = {
            "id": "wallet123",
            "name": "Test Wallet",
            "user": "testuser",
            "adminkey": "admin123",
            "inkey": "invoice123",
            "balance_msat": 1000000,
        }
        schema = LNbitsWalletResponse(**data)
        assert schema.id == "wallet123"
        assert schema.name == "Test Wallet"
        assert schema.balance_msat == 1000000

    def test_invoice_create_request_valid(self):
        """Test valid invoice creation request."""
        data = {
            "amount": 1000,
            "memo": "Test payment",
            "unit": "sat",
            "expiry": 3600,
        }
        schema = LNbitsInvoiceCreateRequest(**data)
        assert schema.amount == 1000
        assert schema.memo == "Test payment"
        assert schema.unit == "sat"
        assert schema.expiry == 3600

    def test_invoice_create_request_invalid_amount(self):
        """Test invoice creation with invalid amount."""
        data = {"amount": 0}  # Must be greater than 0
        with pytest.raises(ValidationError):
            LNbitsInvoiceCreateRequest(**data)

    def test_invoice_response(self):
        """Test invoice response schema."""
        data = {
            "payment_hash": "hash123",
            "payment_request": "lnbc1000n...",
            "checking_id": "check123",
        }
        schema = LNbitsInvoiceResponse(**data)
        assert schema.payment_hash == "hash123"
        assert schema.payment_request == "lnbc1000n..."

    def test_payment_status_response(self):
        """Test payment status response schema."""
        data = {
            "checking_id": "check123",
            "pending": False,
            "amount": 1000,
            "memo": "Test payment",
            "time": 1234567890,
            "payment_hash": "hash123",
            "wallet_id": "wallet123",
        }
        schema = LNbitsPaymentStatusResponse(**data)
        assert schema.checking_id == "check123"
        assert schema.pending is False
        assert schema.amount == 1000

    def test_decode_invoice_request(self):
        """Test decode invoice request schema."""
        data = {"payment_request": "lnbc1000n..."}
        schema = LNbitsDecodeInvoiceRequest(**data)
        assert schema.payment_request == "lnbc1000n..."

    def test_decode_invoice_response(self):
        """Test decode invoice response schema."""
        data = {
            "payment_hash": "hash123",
            "amount_msat": 1000000,
            "date": 1234567890,
            "expiry": 3600,
        }
        schema = LNbitsDecodeInvoiceResponse(**data)
        assert schema.payment_hash == "hash123"
        assert schema.amount_msat == 1000000

    def test_balance_response(self):
        """Test balance response schema."""
        data = {
            "balance": 5000000,
            "currency": "msat",
        }
        schema = LNbitsBalanceResponse(**data)
        assert schema.balance == 5000000
        assert schema.currency == "msat"

    def test_internal_transfer_request_valid(self):
        """Test valid internal transfer request."""
        from uuid import uuid4

        data = {
            "destination_wallet_id": "wallet123",
            "amount": 1000,
            "memo": "Test transfer",
        }
        schema = LNbitsInternalTransferRequest(**data)
        assert schema.amount == 1000
        assert schema.memo == "Test transfer"

    def test_internal_transfer_request_invalid_amount(self):
        """Test internal transfer with invalid amount."""
        data = {
            "destination_wallet_id": "wallet123",
            "amount": 0,  # Must be greater than 0
        }
        with pytest.raises(ValidationError):
            LNbitsInternalTransferRequest(**data)

    def test_internal_transfer_response(self):
        """Test internal transfer response schema."""
        data = {
            "payment_hash": "hash123",
            "checking_id": "check123",
            "amount": 1000,
            "fee": 0,
        }
        schema = LNbitsInternalTransferResponse(**data)
        assert schema.amount == 1000
        assert schema.fee == 0
        assert schema.payment_hash == "hash123"

    def test_payment_request(self):
        """Test payment request schema."""
        data = {
            "bolt11": "lnbc1000n...",
            "out": True,
        }
        schema = LNbitsPaymentRequest(**data)
        assert schema.bolt11 == "lnbc1000n..."
        assert schema.out is True

    def test_payment_status_request(self):
        """Test payment status request schema."""
        data = {"payment_hash": "hash123"}
        schema = LNbitsPaymentStatusRequest(**data)
        assert schema.payment_hash == "hash123"

    def test_wallet_details_response(self):
        """Test wallet details response schema."""
        data = {
            "id": "wallet123",
            "name": "Test Wallet",
            "balance": 5000000,
        }
        schema = LNbitsWalletDetailsResponse(**data)
        assert schema.id == "wallet123"
        assert schema.name == "Test Wallet"
        assert schema.balance == 5000000
