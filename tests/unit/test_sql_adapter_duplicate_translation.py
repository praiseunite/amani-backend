"""Unit tests for SQL adapter IntegrityError to DuplicateEntryError translation."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from datetime import datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy import MetaData

from app.adapters.sql.wallet_registry import SQLWalletRegistry
from app.domain.entities import WalletRegistryEntry, WalletProvider
from app.errors import DuplicateEntryError


class TestSQLAdapterDuplicateTranslation:
    """Test suite for SQL adapter error translation."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock async session."""
        session = AsyncMock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        return session

    @pytest.fixture
    def metadata(self):
        """Create SQLAlchemy metadata."""
        return MetaData()

    @pytest.fixture
    def sql_adapter(self, mock_session, metadata):
        """Create SQL wallet registry adapter with mocked session."""
        return SQLWalletRegistry(session=mock_session, metadata=metadata)

    @pytest.mark.asyncio
    async def test_integrity_error_translated_to_duplicate_entry_error(
        self, sql_adapter, mock_session
    ):
        """Test that IntegrityError is translated to DuplicateEntryError."""
        # Create a wallet entry
        entry = WalletRegistryEntry(
            id=uuid4(),
            user_id=uuid4(),
            provider=WalletProvider.FINCRA,
            provider_account_id="wallet_123",
            provider_customer_id="customer_456",
            metadata={"test": "data"},
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # Mock the session.execute to raise IntegrityError
        mock_session.execute = AsyncMock(
            side_effect=IntegrityError(
                statement="INSERT INTO wallet_registry...",
                params={},
                orig=Exception("duplicate key value violates unique constraint"),
            )
        )

        # Attempt to register should raise DuplicateEntryError, not IntegrityError
        with pytest.raises(DuplicateEntryError) as exc_info:
            await sql_adapter.register(entry=entry, idempotency_key="test_key")

        # Verify the error message
        assert "Duplicate wallet registration detected" in str(exc_info.value)

        # Verify rollback was called
        mock_session.rollback.assert_called_once()

        # Verify the original error is preserved as __cause__
        assert isinstance(exc_info.value.__cause__, IntegrityError)

    @pytest.mark.asyncio
    async def test_integrity_error_with_idempotency_key(
        self, sql_adapter, mock_session
    ):
        """Test IntegrityError translation when duplicate idempotency_key."""
        entry = WalletRegistryEntry(
            id=uuid4(),
            user_id=uuid4(),
            provider=WalletProvider.PAYSTACK,
            provider_account_id="wallet_789",
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # Mock IntegrityError for duplicate idempotency_key
        mock_session.execute = AsyncMock(
            side_effect=IntegrityError(
                statement="INSERT INTO wallet_registry...",
                params={},
                orig=Exception(
                    'duplicate key value violates unique constraint "wallet_registry_idempotency_key_key"'
                ),
            )
        )

        with pytest.raises(DuplicateEntryError):
            await sql_adapter.register(entry=entry, idempotency_key="duplicate_key")

        # Verify rollback was called
        mock_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_successful_registration_no_error(self, sql_adapter, mock_session):
        """Test that successful registration doesn't raise any error."""
        entry = WalletRegistryEntry(
            id=uuid4(),
            user_id=uuid4(),
            provider=WalletProvider.FLUTTERWAVE,
            provider_account_id="wallet_abc",
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # Mock successful execution
        mock_result = MagicMock()
        mock_row = MagicMock()
        # Set up _mapping attribute for the mock row
        mock_row._mapping = {
            "external_id": entry.id,
            "user_id": entry.user_id,
            "provider": entry.provider.value,
            "provider_account_id": entry.provider_account_id,
            "provider_customer_id": entry.provider_customer_id,
            "metadata": entry.metadata,
            "is_active": entry.is_active,
            "created_at": entry.created_at,
            "updated_at": entry.updated_at,
        }
        mock_result.fetchone = MagicMock(return_value=mock_row)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Should not raise any error
        result = await sql_adapter.register(entry=entry, idempotency_key="unique_key")

        # Verify result
        assert result is not None
        assert result.id == entry.id
        assert result.user_id == entry.user_id
        assert result.provider == entry.provider

        # Verify commit was called
        mock_session.commit.assert_called_once()
        # Verify rollback was NOT called
        mock_session.rollback.assert_not_called()

    @pytest.mark.asyncio
    async def test_row_mapping_access_used(self, sql_adapter, mock_session):
        """Test that _row_to_entry uses row._mapping for safe access."""
        entry = WalletRegistryEntry(
            id=uuid4(),
            user_id=uuid4(),
            provider=WalletProvider.FINCRA,
            provider_account_id="wallet_xyz",
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # Create a mock row with _mapping attribute
        mock_result = MagicMock()
        mock_row = MagicMock()
        mock_row._mapping = {
            "external_id": entry.id,
            "user_id": entry.user_id,
            "provider": entry.provider.value,
            "provider_account_id": entry.provider_account_id,
            "provider_customer_id": None,
            "metadata": None,
            "is_active": entry.is_active,
            "created_at": entry.created_at,
            "updated_at": entry.updated_at,
        }
        mock_result.fetchone = MagicMock(return_value=mock_row)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Register entry
        result = await sql_adapter.register(entry=entry)

        # Verify that row._mapping was accessed (indirectly by successful conversion)
        assert result.id == entry.id
        assert result.metadata == {}  # Should default to empty dict for None
