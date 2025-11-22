"""
Unit tests for wallet schemas.
"""

import pytest
from decimal import Decimal
from uuid import uuid4
from datetime import datetime
from pydantic import ValidationError

from app.schemas.wallet import (
    WalletProvider,
    WalletEventType,
    WalletRegistryCreate,
    WalletRegistryResponse,
    WalletBalanceSnapshotCreate,
    WalletBalanceSnapshotResponse,
    WalletTransactionEventCreate,
    WalletTransactionEventResponse,
    WalletSyncRequest,
)


class TestWalletSchemas:
    """Test wallet schema validation."""

    def test_wallet_provider_enum(self):
        """Test wallet provider enum values."""
        assert WalletProvider.FINCRA == "fincra"
        assert WalletProvider.PAYSTACK == "paystack"
        assert WalletProvider.FLUTTERWAVE == "flutterwave"

    def test_wallet_event_type_enum(self):
        """Test wallet event type enum values."""
        assert WalletEventType.DEPOSIT == "deposit"
        assert WalletEventType.WITHDRAWAL == "withdrawal"
        assert WalletEventType.TRANSFER_IN == "transfer_in"
        assert WalletEventType.TRANSFER_OUT == "transfer_out"

    def test_wallet_registry_create_valid(self):
        """Test valid wallet registry creation schema."""
        user_id = uuid4()
        data = {
            "user_id": user_id,
            "provider": WalletProvider.FINCRA,
            "provider_account_id": "fincra-account-123",
            "provider_customer_id": "fincra-customer-456",
            "metadata": {"key": "value"},
        }

        schema = WalletRegistryCreate(**data)
        assert schema.user_id == user_id
        assert schema.provider == WalletProvider.FINCRA
        assert schema.provider_account_id == "fincra-account-123"
        assert schema.provider_customer_id == "fincra-customer-456"
        assert schema.metadata == {"key": "value"}

    def test_wallet_registry_create_missing_required_fields(self):
        """Test wallet registry creation with missing required fields."""
        with pytest.raises(ValidationError) as exc_info:
            WalletRegistryCreate(
                user_id=uuid4(),
                provider=WalletProvider.FINCRA,
                # Missing provider_account_id
            )

        errors = exc_info.value.errors()
        assert any(error["loc"][0] == "provider_account_id" for error in errors)

    def test_wallet_registry_create_empty_provider_account_id(self):
        """Test wallet registry creation with empty provider_account_id."""
        with pytest.raises(ValidationError):
            WalletRegistryCreate(
                user_id=uuid4(),
                provider=WalletProvider.FINCRA,
                provider_account_id="",  # Empty string not allowed
            )

    def test_wallet_balance_snapshot_create_valid(self):
        """Test valid wallet balance snapshot creation schema."""
        wallet_id = uuid4()
        data = {
            "wallet_id": wallet_id,
            "provider": WalletProvider.FINCRA,
            "balance": Decimal("1000.50"),
            "currency": "USD",
            "external_balance_id": "balance-123",
            "as_of": datetime.utcnow(),
            "metadata": {"source": "sync"},
            "idempotency_key": "idem-key-123",
        }

        schema = WalletBalanceSnapshotCreate(**data)
        assert schema.wallet_id == wallet_id
        assert schema.provider == WalletProvider.FINCRA
        assert schema.balance == Decimal("1000.50")
        assert schema.currency == "USD"

    def test_wallet_balance_snapshot_create_negative_balance(self):
        """Test wallet balance snapshot with negative balance."""
        with pytest.raises(ValidationError):
            WalletBalanceSnapshotCreate(
                wallet_id=uuid4(),
                provider=WalletProvider.FINCRA,
                balance=Decimal("-100.00"),  # Negative not allowed
                currency="USD",
            )

    def test_wallet_balance_snapshot_create_invalid_currency(self):
        """Test wallet balance snapshot with invalid currency code."""
        with pytest.raises(ValidationError):
            WalletBalanceSnapshotCreate(
                wallet_id=uuid4(),
                provider=WalletProvider.FINCRA,
                balance=Decimal("1000.00"),
                currency="US",  # Must be 3 characters
            )

    def test_wallet_transaction_event_create_valid(self):
        """Test valid wallet transaction event creation schema."""
        wallet_id = uuid4()
        occurred_at = datetime.utcnow()
        data = {
            "wallet_id": wallet_id,
            "provider": WalletProvider.FINCRA,
            "event_type": WalletEventType.DEPOSIT,
            "amount": Decimal("500.00"),
            "currency": "USD",
            "occurred_at": occurred_at,
            "provider_event_id": "event-123",
            "metadata": {"source": "bank_transfer"},
            "idempotency_key": "idem-key-456",
        }

        schema = WalletTransactionEventCreate(**data)
        assert schema.wallet_id == wallet_id
        assert schema.event_type == WalletEventType.DEPOSIT
        assert schema.amount == Decimal("500.00")
        assert schema.occurred_at == occurred_at

    def test_wallet_transaction_event_create_zero_amount(self):
        """Test wallet transaction event with zero amount."""
        with pytest.raises(ValidationError):
            WalletTransactionEventCreate(
                wallet_id=uuid4(),
                provider=WalletProvider.FINCRA,
                event_type=WalletEventType.DEPOSIT,
                amount=Decimal("0.00"),  # Must be greater than 0
                currency="USD",
                occurred_at=datetime.utcnow(),
            )

    def test_wallet_sync_request_valid(self):
        """Test valid wallet sync request schema."""
        wallet_id = uuid4()
        schema = WalletSyncRequest(
            wallet_id=wallet_id,
            idempotency_key="sync-key-789",
        )

        assert schema.wallet_id == wallet_id
        assert schema.idempotency_key == "sync-key-789"

    def test_wallet_sync_request_without_idempotency_key(self):
        """Test wallet sync request without idempotency key."""
        wallet_id = uuid4()
        schema = WalletSyncRequest(wallet_id=wallet_id)

        assert schema.wallet_id == wallet_id
        assert schema.idempotency_key is None


class TestWalletResponseSchemas:
    """Test wallet response schema serialization."""

    def test_wallet_registry_response_from_attributes(self):
        """Test wallet registry response from ORM model."""
        from app.models.wallet_registry import WalletRegistry

        external_uuid = uuid4()
        wallet = WalletRegistry(
            id=1,
            external_id=external_uuid,
            user_id=uuid4(),
            provider="fincra",
            provider_account_id="account-123",
            is_active=True,
            extra_data={"key": "value"},  # Use extra_data instead of metadata
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # Test that response schema can serialize from ORM model
        # Note: WalletRegistryResponse expects 'id' field to map to external_id
        response = WalletRegistryResponse(
            id=wallet.external_id,
            external_id=wallet.external_id,
            user_id=wallet.user_id,
            provider=wallet.provider,
            provider_account_id=wallet.provider_account_id,
            is_active=wallet.is_active,
            metadata=wallet.extra_data,
            created_at=wallet.created_at,
            updated_at=wallet.updated_at,
        )
        assert response.id == external_uuid
        assert response.provider == wallet.provider

    def test_wallet_balance_snapshot_response_from_attributes(self):
        """Test wallet balance snapshot response from ORM model."""
        from app.models.wallet_balance_snapshot import WalletBalanceSnapshot

        snapshot = WalletBalanceSnapshot(
            id=uuid4(),
            wallet_id=uuid4(),
            provider="fincra",
            balance=Decimal("1500.00"),
            currency="USD",
            as_of=datetime.utcnow(),
            extra_data={"source": "sync"},  # Use extra_data instead of metadata
            created_at=datetime.utcnow(),
        )

        # Test that response schema can serialize from ORM model
        response = WalletBalanceSnapshotResponse(
            id=snapshot.id,
            wallet_id=snapshot.wallet_id,
            provider=snapshot.provider,
            balance=snapshot.balance,
            currency=snapshot.currency,
            as_of=snapshot.as_of,
            metadata=snapshot.extra_data,
            created_at=snapshot.created_at,
        )
        assert response.id == snapshot.id
        assert response.balance == snapshot.balance
