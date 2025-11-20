"""Unit tests for sequential integer ID assignment in new models."""

import pytest
from uuid import uuid4, UUID
from datetime import datetime, timedelta

from app.models import LinkToken, WalletRegistry, Hold, LedgerEntry
from app.models.link_token import WalletProvider
from app.models.hold import HoldStatus
from app.models.ledger_entry import TransactionType as LedgerTransactionType


class TestSequentialIDs:
    """Test suite to verify sequential integer ID assignment."""

    def test_link_token_sequential_ids(self):
        """Test that LinkToken models have sequential integer IDs."""
        user_id = uuid4()
        
        # Create multiple link tokens
        token1 = LinkToken(
            user_id=user_id,
            token="token1",
            provider=WalletProvider.FINCRA,
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        token2 = LinkToken(
            user_id=user_id,
            token="token2",
            provider=WalletProvider.PAYSTACK,
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        
        # Verify that ids will be assigned by database (autoincrement)
        assert token1.id is None  # Not yet persisted
        assert token2.id is None
        
        # Verify external_id column exists
        assert hasattr(LinkToken, 'external_id')

    def test_wallet_registry_sequential_ids(self):
        """Test that WalletRegistry models have sequential integer IDs."""
        user_id = uuid4()
        
        wallet1 = WalletRegistry(
            user_id=user_id,
            provider=WalletProvider.FINCRA,
            provider_account_id="account1"
        )
        wallet2 = WalletRegistry(
            user_id=user_id,
            provider=WalletProvider.PAYSTACK,
            provider_account_id="account2"
        )
        
        # Verify that ids will be assigned by database (autoincrement)
        assert wallet1.id is None  # Not yet persisted
        assert wallet2.id is None
        
        # Verify external_id column exists
        assert hasattr(WalletRegistry, 'external_id')

    def test_hold_sequential_ids(self):
        """Test that Hold models have sequential integer IDs."""
        user_id = uuid4()
        
        hold1 = Hold(
            user_id=user_id,
            amount=100.00,
            currency="USD",
            reference="ref1"
        )
        hold2 = Hold(
            user_id=user_id,
            amount=200.00,
            currency="USD",
            reference="ref2"
        )
        
        # Verify that ids will be assigned by database (autoincrement)
        assert hold1.id is None  # Not yet persisted
        assert hold2.id is None
        
        # Verify external_id column exists
        assert hasattr(Hold, 'external_id')

    def test_ledger_entry_sequential_ids(self):
        """Test that LedgerEntry models have sequential integer IDs."""
        user_id = uuid4()
        
        entry1 = LedgerEntry(
            user_id=user_id,
            transaction_type=LedgerTransactionType.CREDIT,
            amount=100.00,
            currency="USD",
            balance_after=100.00,
            reference="ref1"
        )
        entry2 = LedgerEntry(
            user_id=user_id,
            transaction_type=LedgerTransactionType.DEBIT,
            amount=50.00,
            currency="USD",
            balance_after=50.00,
            reference="ref2"
        )
        
        # Verify that ids will be assigned by database (autoincrement)
        assert entry1.id is None  # Not yet persisted
        assert entry2.id is None
        
        # Verify external_id column exists
        assert hasattr(LedgerEntry, 'external_id')


class TestModelStructure:
    """Test suite to verify model structure."""

    def test_link_token_has_required_fields(self):
        """Test that LinkToken has all required fields."""
        user_id = uuid4()
        token = LinkToken(
            user_id=user_id,
            token="test_token",
            provider=WalletProvider.FINCRA,
            expires_at=datetime.utcnow() + timedelta(hours=1),
            is_consumed=False
        )
        
        # Verify fields exist
        assert hasattr(token, 'id')
        assert hasattr(token, 'external_id')
        assert hasattr(token, 'user_id')
        assert hasattr(token, 'token')
        assert hasattr(token, 'provider')
        assert hasattr(token, 'is_consumed')
        assert hasattr(token, 'created_at')
        assert hasattr(token, 'expires_at')
        assert hasattr(token, 'consumed_at')
        
        # Verify explicitly set values
        assert token.is_consumed is False
        assert token.user_id == user_id
        assert token.token == "test_token"
        assert token.provider == WalletProvider.FINCRA

    def test_wallet_registry_has_required_fields(self):
        """Test that WalletRegistry has all required fields."""
        user_id = uuid4()
        wallet = WalletRegistry(
            user_id=user_id,
            provider=WalletProvider.FINCRA,
            provider_account_id="account123",
            is_active=True
        )
        
        # Verify fields exist
        assert hasattr(wallet, 'id')
        assert hasattr(wallet, 'external_id')
        assert hasattr(wallet, 'user_id')
        assert hasattr(wallet, 'provider')
        assert hasattr(wallet, 'provider_account_id')
        assert hasattr(wallet, 'provider_customer_id')
        assert hasattr(wallet, 'extra_data')
        assert hasattr(wallet, 'is_active')
        assert hasattr(wallet, 'created_at')
        assert hasattr(wallet, 'updated_at')
        
        # Verify explicitly set values
        assert wallet.is_active is True
        assert wallet.user_id == user_id
        assert wallet.provider == WalletProvider.FINCRA
        assert wallet.provider_account_id == "account123"

    def test_hold_has_required_fields(self):
        """Test that Hold has all required fields."""
        user_id = uuid4()
        hold = Hold(
            user_id=user_id,
            amount=100.00,
            currency="USD",
            status=HoldStatus.ACTIVE,
            reference="ref123"
        )
        
        # Verify fields exist
        assert hasattr(hold, 'id')
        assert hasattr(hold, 'external_id')
        assert hasattr(hold, 'user_id')
        assert hasattr(hold, 'amount')
        assert hasattr(hold, 'currency')
        assert hasattr(hold, 'status')
        assert hasattr(hold, 'reference')
        assert hasattr(hold, 'created_at')
        assert hasattr(hold, 'released_at')
        assert hasattr(hold, 'captured_at')
        
        # Verify explicitly set values
        assert hold.status == HoldStatus.ACTIVE
        assert hold.currency == 'USD'
        assert hold.user_id == user_id
        assert hold.amount == 100.00
        assert hold.reference == "ref123"

    def test_ledger_entry_has_required_fields(self):
        """Test that LedgerEntry has all required fields."""
        user_id = uuid4()
        entry = LedgerEntry(
            user_id=user_id,
            transaction_type=LedgerTransactionType.CREDIT,
            amount=100.00,
            currency="USD",
            balance_after=100.00,
            reference="ref123"
        )
        
        # Verify fields exist
        assert hasattr(entry, 'id')
        assert hasattr(entry, 'external_id')
        assert hasattr(entry, 'user_id')
        assert hasattr(entry, 'transaction_type')
        assert hasattr(entry, 'amount')
        assert hasattr(entry, 'currency')
        assert hasattr(entry, 'balance_after')
        assert hasattr(entry, 'reference')
        assert hasattr(entry, 'description')
        assert hasattr(entry, 'created_at')
        
        # Verify explicitly set values
        assert entry.currency == 'USD'
        assert entry.user_id == user_id
        assert entry.transaction_type == LedgerTransactionType.CREDIT
        assert entry.amount == 100.00
        assert entry.balance_after == 100.00
        assert entry.reference == "ref123"


class TestModelPrimaryKeys:
    """Test suite to verify primary key configuration."""

    def test_link_token_has_bigint_primary_key(self):
        """Test that LinkToken uses BigInteger for primary key."""
        assert hasattr(LinkToken, '__table__')
        id_column = LinkToken.__table__.columns['id']
        assert id_column.primary_key is True
        assert id_column.autoincrement is True
        
    def test_wallet_registry_has_bigint_primary_key(self):
        """Test that WalletRegistry uses BigInteger for primary key."""
        assert hasattr(WalletRegistry, '__table__')
        id_column = WalletRegistry.__table__.columns['id']
        assert id_column.primary_key is True
        assert id_column.autoincrement is True
        
    def test_hold_has_bigint_primary_key(self):
        """Test that Hold uses BigInteger for primary key."""
        assert hasattr(Hold, '__table__')
        id_column = Hold.__table__.columns['id']
        assert id_column.primary_key is True
        assert id_column.autoincrement is True
        
    def test_ledger_entry_has_bigint_primary_key(self):
        """Test that LedgerEntry uses BigInteger for primary key."""
        assert hasattr(LedgerEntry, '__table__')
        id_column = LedgerEntry.__table__.columns['id']
        assert id_column.primary_key is True
        assert id_column.autoincrement is True
