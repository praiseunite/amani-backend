"""
Comprehensive unit tests for app.domain.entities module.
Tests domain entity dataclasses and enums.
"""

import pytest
from datetime import datetime
from uuid import UUID, uuid4
from app.domain.entities import (
    WalletProvider,
    HoldStatus,
    TransactionType,
    WalletEventType,
    User,
    LinkToken,
    WalletRegistryEntry,
    Hold,
    LedgerEntry,
    WalletBalanceSnapshot,
    WalletTransactionEvent,
)


class TestEnums:
    """Test suite for domain enums."""

    def test_wallet_provider_values(self):
        """Test WalletProvider enum values."""
        assert WalletProvider.FINCRA.value == "fincra"
        assert WalletProvider.PAYSTACK.value == "paystack"
        assert WalletProvider.FLUTTERWAVE.value == "flutterwave"

    def test_wallet_provider_all_members(self):
        """Test all WalletProvider members."""
        providers = [p.value for p in WalletProvider]
        assert "fincra" in providers
        assert "paystack" in providers
        assert "flutterwave" in providers
        assert len(providers) == 3

    def test_hold_status_values(self):
        """Test HoldStatus enum values."""
        assert HoldStatus.ACTIVE.value == "active"
        assert HoldStatus.RELEASED.value == "released"
        assert HoldStatus.CAPTURED.value == "captured"

    def test_hold_status_all_members(self):
        """Test all HoldStatus members."""
        statuses = [s.value for s in HoldStatus]
        assert "active" in statuses
        assert "released" in statuses
        assert "captured" in statuses
        assert len(statuses) == 3

    def test_transaction_type_values(self):
        """Test TransactionType enum values."""
        assert TransactionType.DEBIT.value == "debit"
        assert TransactionType.CREDIT.value == "credit"

    def test_transaction_type_all_members(self):
        """Test all TransactionType members."""
        types = [t.value for t in TransactionType]
        assert "debit" in types
        assert "credit" in types
        assert len(types) == 2

    def test_wallet_event_type_values(self):
        """Test WalletEventType enum values."""
        assert WalletEventType.DEPOSIT.value == "deposit"
        assert WalletEventType.WITHDRAWAL.value == "withdrawal"
        assert WalletEventType.TRANSFER_IN.value == "transfer_in"
        assert WalletEventType.TRANSFER_OUT.value == "transfer_out"
        assert WalletEventType.FEE.value == "fee"
        assert WalletEventType.REFUND.value == "refund"
        assert WalletEventType.HOLD.value == "hold"
        assert WalletEventType.RELEASE.value == "release"

    def test_wallet_event_type_all_members(self):
        """Test all WalletEventType members."""
        event_types = [e.value for e in WalletEventType]
        assert len(event_types) == 8


class TestUser:
    """Test suite for User entity."""

    def test_user_initialization_with_defaults(self):
        """Test User initialization with default values."""
        user = User()
        
        assert isinstance(user.id, UUID)
        assert user.external_id is None
        assert user.email == ""
        assert user.full_name is None
        assert user.role == "client"
        assert user.is_active is True
        assert user.is_verified is False
        assert isinstance(user.created_at, datetime)
        assert isinstance(user.updated_at, datetime)

    def test_user_initialization_with_values(self):
        """Test User initialization with custom values."""
        user_id = uuid4()
        created_at = datetime(2024, 1, 1, 10, 0, 0)
        
        user = User(
            id=user_id,
            external_id="ext_123",
            email="test@example.com",
            full_name="John Doe",
            role="admin",
            is_active=False,
            is_verified=True,
            created_at=created_at,
            updated_at=created_at,
        )
        
        assert user.id == user_id
        assert user.external_id == "ext_123"
        assert user.email == "test@example.com"
        assert user.full_name == "John Doe"
        assert user.role == "admin"
        assert user.is_active is False
        assert user.is_verified is True
        assert user.created_at == created_at

    def test_user_unique_ids(self):
        """Test that Users get unique IDs."""
        user1 = User()
        user2 = User()
        
        assert user1.id != user2.id


class TestLinkToken:
    """Test suite for LinkToken entity."""

    def test_link_token_initialization_defaults(self):
        """Test LinkToken with default values."""
        token = LinkToken()
        
        assert isinstance(token.id, UUID)
        assert isinstance(token.user_id, UUID)
        assert token.token == ""
        assert token.provider == WalletProvider.FINCRA
        assert isinstance(token.expires_at, datetime)
        assert token.is_consumed is False
        assert isinstance(token.created_at, datetime)
        assert token.consumed_at is None

    def test_link_token_initialization_with_values(self):
        """Test LinkToken with custom values."""
        token_id = uuid4()
        user_id = uuid4()
        expires_at = datetime(2024, 12, 31, 23, 59, 59)
        consumed_at = datetime(2024, 6, 1, 10, 0, 0)
        
        token = LinkToken(
            id=token_id,
            user_id=user_id,
            token="secure_token_123",
            provider=WalletProvider.PAYSTACK,
            expires_at=expires_at,
            is_consumed=True,
            consumed_at=consumed_at,
        )
        
        assert token.id == token_id
        assert token.user_id == user_id
        assert token.token == "secure_token_123"
        assert token.provider == WalletProvider.PAYSTACK
        assert token.expires_at == expires_at
        assert token.is_consumed is True
        assert token.consumed_at == consumed_at

    def test_link_token_different_providers(self):
        """Test LinkToken with different providers."""
        token_fincra = LinkToken(provider=WalletProvider.FINCRA)
        token_paystack = LinkToken(provider=WalletProvider.PAYSTACK)
        token_flutter = LinkToken(provider=WalletProvider.FLUTTERWAVE)
        
        assert token_fincra.provider == WalletProvider.FINCRA
        assert token_paystack.provider == WalletProvider.PAYSTACK
        assert token_flutter.provider == WalletProvider.FLUTTERWAVE


class TestWalletRegistryEntry:
    """Test suite for WalletRegistryEntry entity."""

    def test_wallet_registry_entry_defaults(self):
        """Test WalletRegistryEntry with defaults."""
        entry = WalletRegistryEntry()
        
        assert isinstance(entry.id, UUID)
        assert isinstance(entry.user_id, UUID)
        assert entry.provider == WalletProvider.FINCRA
        assert entry.provider_account_id == ""
        assert entry.provider_customer_id is None
        assert entry.metadata == {}
        assert entry.is_active is True
        assert isinstance(entry.created_at, datetime)
        assert isinstance(entry.updated_at, datetime)

    def test_wallet_registry_entry_with_values(self):
        """Test WalletRegistryEntry with custom values."""
        entry_id = uuid4()
        user_id = uuid4()
        metadata = {"account_type": "business", "verified": True}
        
        entry = WalletRegistryEntry(
            id=entry_id,
            user_id=user_id,
            provider=WalletProvider.PAYSTACK,
            provider_account_id="acc_123456",
            provider_customer_id="cust_789",
            metadata=metadata,
            is_active=False,
        )
        
        assert entry.id == entry_id
        assert entry.user_id == user_id
        assert entry.provider == WalletProvider.PAYSTACK
        assert entry.provider_account_id == "acc_123456"
        assert entry.provider_customer_id == "cust_789"
        assert entry.metadata == metadata
        assert entry.is_active is False

    def test_wallet_registry_entry_metadata_default_mutable(self):
        """Test that metadata dict is not shared between instances."""
        entry1 = WalletRegistryEntry()
        entry2 = WalletRegistryEntry()
        
        entry1.metadata["key"] = "value"
        
        assert "key" in entry1.metadata
        assert "key" not in entry2.metadata


class TestHold:
    """Test suite for Hold entity."""

    def test_hold_defaults(self):
        """Test Hold with default values."""
        hold = Hold()
        
        assert isinstance(hold.id, UUID)
        assert isinstance(hold.user_id, UUID)
        assert hold.amount == 0.0
        assert hold.currency == "USD"
        assert hold.status == HoldStatus.ACTIVE
        assert hold.reference == ""
        assert isinstance(hold.created_at, datetime)
        assert hold.released_at is None
        assert hold.captured_at is None

    def test_hold_with_values(self):
        """Test Hold with custom values."""
        hold_id = uuid4()
        user_id = uuid4()
        released_at = datetime(2024, 6, 1, 10, 0, 0)
        
        hold = Hold(
            id=hold_id,
            user_id=user_id,
            amount=1500.50,
            currency="NGN",
            status=HoldStatus.RELEASED,
            reference="hold_ref_123",
            released_at=released_at,
        )
        
        assert hold.id == hold_id
        assert hold.user_id == user_id
        assert hold.amount == 1500.50
        assert hold.currency == "NGN"
        assert hold.status == HoldStatus.RELEASED
        assert hold.reference == "hold_ref_123"
        assert hold.released_at == released_at

    def test_hold_different_statuses(self):
        """Test Hold with different statuses."""
        hold_active = Hold(status=HoldStatus.ACTIVE)
        hold_released = Hold(status=HoldStatus.RELEASED)
        hold_captured = Hold(status=HoldStatus.CAPTURED)
        
        assert hold_active.status == HoldStatus.ACTIVE
        assert hold_released.status == HoldStatus.RELEASED
        assert hold_captured.status == HoldStatus.CAPTURED


class TestLedgerEntry:
    """Test suite for LedgerEntry entity."""

    def test_ledger_entry_defaults(self):
        """Test LedgerEntry with defaults."""
        entry = LedgerEntry()
        
        assert isinstance(entry.id, UUID)
        assert isinstance(entry.user_id, UUID)
        assert entry.transaction_type == TransactionType.CREDIT
        assert entry.amount == 0.0
        assert entry.currency == "USD"
        assert entry.balance_after == 0.0
        assert entry.reference == ""
        assert entry.description == ""
        assert isinstance(entry.created_at, datetime)

    def test_ledger_entry_with_values(self):
        """Test LedgerEntry with custom values."""
        entry_id = uuid4()
        user_id = uuid4()
        
        entry = LedgerEntry(
            id=entry_id,
            user_id=user_id,
            transaction_type=TransactionType.DEBIT,
            amount=250.75,
            currency="EUR",
            balance_after=1749.25,
            reference="txn_ref_456",
            description="Payment for services",
        )
        
        assert entry.id == entry_id
        assert entry.user_id == user_id
        assert entry.transaction_type == TransactionType.DEBIT
        assert entry.amount == 250.75
        assert entry.currency == "EUR"
        assert entry.balance_after == 1749.25
        assert entry.reference == "txn_ref_456"
        assert entry.description == "Payment for services"

    def test_ledger_entry_transaction_types(self):
        """Test LedgerEntry with different transaction types."""
        credit = LedgerEntry(transaction_type=TransactionType.CREDIT)
        debit = LedgerEntry(transaction_type=TransactionType.DEBIT)
        
        assert credit.transaction_type == TransactionType.CREDIT
        assert debit.transaction_type == TransactionType.DEBIT


class TestWalletBalanceSnapshot:
    """Test suite for WalletBalanceSnapshot entity."""

    def test_wallet_balance_snapshot_with_values(self):
        """Test WalletBalanceSnapshot initialization."""
        wallet_id = uuid4()
        as_of = datetime(2024, 6, 1, 12, 0, 0)
        metadata = {"source": "api", "version": "v1"}
        
        snapshot = WalletBalanceSnapshot(
            wallet_id=wallet_id,
            provider=WalletProvider.FINCRA,
            balance=5000.00,
            currency="USD",
            as_of=as_of,
            metadata=metadata,
        )
        
        assert snapshot.wallet_id == wallet_id
        assert snapshot.provider == WalletProvider.FINCRA
        assert snapshot.balance == 5000.00
        assert snapshot.currency == "USD"
        assert snapshot.as_of == as_of
        assert snapshot.metadata == metadata
        assert isinstance(snapshot.id, UUID)
        assert isinstance(snapshot.created_at, datetime)
        assert snapshot.external_balance_id is None

    def test_wallet_balance_snapshot_with_external_id(self):
        """Test WalletBalanceSnapshot with external balance ID."""
        wallet_id = uuid4()
        as_of = datetime.utcnow()
        
        snapshot = WalletBalanceSnapshot(
            wallet_id=wallet_id,
            provider=WalletProvider.PAYSTACK,
            balance=1000.00,
            currency="NGN",
            as_of=as_of,
            metadata={},
            external_balance_id="ext_bal_123",
        )
        
        assert snapshot.external_balance_id == "ext_bal_123"


class TestWalletTransactionEvent:
    """Test suite for WalletTransactionEvent entity."""

    def test_wallet_transaction_event_defaults(self):
        """Test WalletTransactionEvent with defaults."""
        event = WalletTransactionEvent()
        
        assert isinstance(event.id, UUID)
        assert isinstance(event.wallet_id, UUID)
        assert event.provider == WalletProvider.FINCRA
        assert event.event_type == WalletEventType.DEPOSIT
        assert event.amount == 0.0
        assert event.currency == "USD"
        assert event.provider_event_id is None
        assert event.metadata == {}
        assert isinstance(event.occurred_at, datetime)
        assert isinstance(event.created_at, datetime)

    def test_wallet_transaction_event_with_values(self):
        """Test WalletTransactionEvent with custom values."""
        event_id = uuid4()
        wallet_id = uuid4()
        occurred_at = datetime(2024, 6, 1, 15, 30, 0)
        metadata = {"fee_amount": 2.50, "reference": "ref_123"}
        
        event = WalletTransactionEvent(
            id=event_id,
            wallet_id=wallet_id,
            provider=WalletProvider.FLUTTERWAVE,
            event_type=WalletEventType.WITHDRAWAL,
            amount=500.00,
            currency="GBP",
            provider_event_id="evt_456",
            metadata=metadata,
            occurred_at=occurred_at,
        )
        
        assert event.id == event_id
        assert event.wallet_id == wallet_id
        assert event.provider == WalletProvider.FLUTTERWAVE
        assert event.event_type == WalletEventType.WITHDRAWAL
        assert event.amount == 500.00
        assert event.currency == "GBP"
        assert event.provider_event_id == "evt_456"
        assert event.metadata == metadata
        assert event.occurred_at == occurred_at

    def test_wallet_transaction_event_different_types(self):
        """Test WalletTransactionEvent with different event types."""
        deposit = WalletTransactionEvent(event_type=WalletEventType.DEPOSIT)
        withdrawal = WalletTransactionEvent(event_type=WalletEventType.WITHDRAWAL)
        transfer_in = WalletTransactionEvent(event_type=WalletEventType.TRANSFER_IN)
        transfer_out = WalletTransactionEvent(event_type=WalletEventType.TRANSFER_OUT)
        
        assert deposit.event_type == WalletEventType.DEPOSIT
        assert withdrawal.event_type == WalletEventType.WITHDRAWAL
        assert transfer_in.event_type == WalletEventType.TRANSFER_IN
        assert transfer_out.event_type == WalletEventType.TRANSFER_OUT

    def test_wallet_transaction_event_metadata_isolation(self):
        """Test metadata dict is isolated between instances."""
        event1 = WalletTransactionEvent()
        event2 = WalletTransactionEvent()
        
        event1.metadata["key1"] = "value1"
        event2.metadata["key2"] = "value2"
        
        assert "key1" in event1.metadata
        assert "key1" not in event2.metadata
        assert "key2" in event2.metadata
        assert "key2" not in event1.metadata
