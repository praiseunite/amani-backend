"""
Unit tests for FinCra payment schemas.
"""

import pytest
from decimal import Decimal
from datetime import datetime
from pydantic import ValidationError

from app.schemas.fincra import (
    FinCraPaymentRequest,
    FinCraPaymentResponse,
    FinCraPaymentVerifyRequest,
    FinCraTransferRequest,
    FinCraTransferResponse,
    FinCraBalanceRequest,
    FinCraBalanceResponse,
)


class TestFinCraPaymentSchemas:
    """Test FinCra payment schema validation."""

    def test_payment_request_valid(self):
        """Test valid FinCra payment request schema."""
        data = {
            "amount": Decimal("1000.00"),
            "currency": "USD",
            "customer_email": "customer@example.com",
            "reference": "pay-ref-123",
            "description": "Payment for services",
            "metadata": {"order_id": "order-456"},
        }

        schema = FinCraPaymentRequest(**data)
        assert schema.amount == Decimal("1000.00")
        assert schema.currency == "USD"
        assert schema.customer_email == "customer@example.com"
        assert schema.reference == "pay-ref-123"

    def test_payment_request_zero_amount(self):
        """Test payment request with zero amount."""
        with pytest.raises(ValidationError):
            FinCraPaymentRequest(
                amount=Decimal("0.00"),  # Must be greater than 0
                currency="USD",
                customer_email="customer@example.com",
                reference="pay-ref-123",
            )

    def test_payment_request_negative_amount(self):
        """Test payment request with negative amount."""
        with pytest.raises(ValidationError):
            FinCraPaymentRequest(
                amount=Decimal("-100.00"),  # Must be greater than 0
                currency="USD",
                customer_email="customer@example.com",
                reference="pay-ref-123",
            )

    def test_payment_request_invalid_email(self):
        """Test payment request with invalid email."""
        with pytest.raises(ValidationError):
            FinCraPaymentRequest(
                amount=Decimal("1000.00"),
                currency="USD",
                customer_email="not-an-email",  # Invalid email format
                reference="pay-ref-123",
            )

    def test_payment_request_invalid_currency_code(self):
        """Test payment request with invalid currency code."""
        with pytest.raises(ValidationError):
            FinCraPaymentRequest(
                amount=Decimal("1000.00"),
                currency="US",  # Must be 3 characters
                customer_email="customer@example.com",
                reference="pay-ref-123",
            )

    def test_payment_request_empty_reference(self):
        """Test payment request with empty reference."""
        with pytest.raises(ValidationError):
            FinCraPaymentRequest(
                amount=Decimal("1000.00"),
                currency="USD",
                customer_email="customer@example.com",
                reference="",  # Cannot be empty
            )

    def test_payment_verify_request_valid(self):
        """Test valid FinCra payment verify request schema."""
        schema = FinCraPaymentVerifyRequest(transaction_id="txn-123")
        assert schema.transaction_id == "txn-123"

    def test_payment_verify_request_empty_transaction_id(self):
        """Test payment verify request with empty transaction ID."""
        with pytest.raises(ValidationError):
            FinCraPaymentVerifyRequest(transaction_id="")


class TestFinCraTransferSchemas:
    """Test FinCra transfer schema validation."""

    def test_transfer_request_valid(self):
        """Test valid FinCra transfer request schema."""
        data = {
            "amount": Decimal("500.00"),
            "currency": "USD",
            "recipient_account": "1234567890",
            "recipient_bank_code": "044",
            "reference": "transfer-ref-123",
            "narration": "Transfer for services",
            "metadata": {"invoice_id": "inv-789"},
        }

        schema = FinCraTransferRequest(**data)
        assert schema.amount == Decimal("500.00")
        assert schema.recipient_account == "1234567890"
        assert schema.recipient_bank_code == "044"
        assert schema.reference == "transfer-ref-123"

    def test_transfer_request_zero_amount(self):
        """Test transfer request with zero amount."""
        with pytest.raises(ValidationError):
            FinCraTransferRequest(
                amount=Decimal("0.00"),  # Must be greater than 0
                currency="USD",
                recipient_account="1234567890",
                recipient_bank_code="044",
                reference="transfer-ref-123",
            )

    def test_transfer_request_empty_recipient_account(self):
        """Test transfer request with empty recipient account."""
        with pytest.raises(ValidationError):
            FinCraTransferRequest(
                amount=Decimal("500.00"),
                currency="USD",
                recipient_account="",  # Cannot be empty
                recipient_bank_code="044",
                reference="transfer-ref-123",
            )

    def test_transfer_request_empty_bank_code(self):
        """Test transfer request with empty bank code."""
        with pytest.raises(ValidationError):
            FinCraTransferRequest(
                amount=Decimal("500.00"),
                currency="USD",
                recipient_account="1234567890",
                recipient_bank_code="",  # Cannot be empty
                reference="transfer-ref-123",
            )


class TestFinCraBalanceSchemas:
    """Test FinCra balance schema validation."""

    def test_balance_request_with_currency(self):
        """Test balance request with currency filter."""
        schema = FinCraBalanceRequest(currency="USD")
        assert schema.currency == "USD"

    def test_balance_request_without_currency(self):
        """Test balance request without currency filter."""
        schema = FinCraBalanceRequest()
        assert schema.currency is None

    def test_balance_request_invalid_currency(self):
        """Test balance request with invalid currency code."""
        with pytest.raises(ValidationError):
            FinCraBalanceRequest(currency="US")  # Must be 3 characters

    def test_balance_response_valid(self):
        """Test valid FinCra balance response schema."""
        data = {
            "currency": "USD",
            "available_balance": Decimal("10000.00"),
            "ledger_balance": Decimal("10500.00"),
            "metadata": {"account_type": "business"},
        }

        schema = FinCraBalanceResponse(**data)
        assert schema.currency == "USD"
        assert schema.available_balance == Decimal("10000.00")
        assert schema.ledger_balance == Decimal("10500.00")


class TestFinCraResponseSchemas:
    """Test FinCra response schema serialization."""

    def test_payment_response_valid(self):
        """Test valid FinCra payment response schema."""
        data = {
            "id": "txn-123",
            "reference": "pay-ref-123",
            "amount": Decimal("1000.00"),
            "currency": "USD",
            "status": "pending",
            "customer_email": "customer@example.com",
            "description": "Payment for services",
            "created_at": datetime.utcnow(),
            "metadata": {"order_id": "order-456"},
        }

        schema = FinCraPaymentResponse(**data)
        assert schema.id == "txn-123"
        assert schema.status == "pending"

    def test_transfer_response_valid(self):
        """Test valid FinCra transfer response schema."""
        data = {
            "id": "transfer-123",
            "reference": "transfer-ref-123",
            "amount": Decimal("500.00"),
            "currency": "USD",
            "status": "processing",
            "recipient_account": "1234567890",
            "recipient_bank_code": "044",
            "narration": "Transfer for services",
            "created_at": datetime.utcnow(),
            "metadata": {"invoice_id": "inv-789"},
        }

        schema = FinCraTransferResponse(**data)
        assert schema.id == "transfer-123"
        assert schema.status == "processing"
        assert schema.recipient_account == "1234567890"
