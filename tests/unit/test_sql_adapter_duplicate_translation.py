"""Unit tests for SQL adapter duplicate error translation."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from sqlalchemy.exc import IntegrityError

from app.domain.entities import WalletRegistryEntry, WalletProvider
from app.adapters.sql.wallet_registry import SQLWalletRegistry
from app.errors import DuplicateEntryError


class TestSQLAdapterDuplicateTranslation:
    """Test suite for SQL adapter IntegrityError translation to DuplicateEntryError."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock async session."""
        session = AsyncMock()
        return session

    @pytest.fixture
    def mock_metadata(self):
        """Create a mock metadata object."""
        from sqlalchemy import MetaData

        return MetaData()

    @pytest.fixture
    def sql_adapter(self, mock_session, mock_metadata):
        """Create SQL wallet registry adapter."""
        return SQLWalletRegistry(mock_session, mock_metadata)

    @pytest.fixture
    def sample_entry(self):
        """Create a sample wallet registry entry."""
        return WalletRegistryEntry(
            id=uuid4(),
            user_id=uuid4(),
            provider=WalletProvider.FINCRA,
            provider_account_id="wallet_123",
            provider_customer_id="customer_456",
            metadata={"test": "data"},
            is_active=True,
        )

    @pytest.mark.asyncio
    async def test_integrity_error_translated_to_duplicate_entry_error(
        self, sql_adapter, sample_entry, mock_session
    ):
        """Test that IntegrityError during insert is translated to DuplicateEntryError."""
        # Mock the session.execute to raise IntegrityError
        integrity_error = IntegrityError(
            "duplicate key value violates unique constraint",
            params=None,
            orig=Exception("UNIQUE constraint failed"),
        )
        mock_session.execute.side_effect = integrity_error

        # Attempt to register should raise DuplicateEntryError, not IntegrityError
        with pytest.raises(DuplicateEntryError) as exc_info:
            await sql_adapter.register(sample_entry, idempotency_key="test_key")

        # Verify the error message
        assert "unique constraint" in str(exc_info.value).lower()

        # Verify the original error is preserved as __cause__
        assert exc_info.value.__cause__ is integrity_error

        # Verify rollback was called
        mock_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_integrity_error_on_duplicate_idempotency_key(
        self, sql_adapter, sample_entry, mock_session
    ):
        """Test IntegrityError translation for duplicate idempotency key."""
        # Mock the session.execute to raise IntegrityError for idempotency_key
        integrity_error = IntegrityError(
            "duplicate key value violates unique constraint wallet_registry_idempotency_key_key",
            params=None,
            orig=Exception("UNIQUE constraint failed on idempotency_key"),
        )
        mock_session.execute.side_effect = integrity_error

        # Should translate to DuplicateEntryError
        with pytest.raises(DuplicateEntryError) as exc_info:
            await sql_adapter.register(sample_entry, idempotency_key="duplicate_key")

        # Verify the original error is preserved
        assert exc_info.value.__cause__ is integrity_error

        # Verify rollback was called
        mock_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_successful_register_returns_entry(self, sql_adapter, sample_entry, mock_session):
        """Test that successful registration returns the entry without errors."""
        # Mock successful execution
        mock_result = MagicMock()
        mock_row = MagicMock()

        # Mock the _mapping property to return dict-like access
        mock_row._mapping = {
            "external_id": sample_entry.id,
            "user_id": sample_entry.user_id,
            "provider": sample_entry.provider.value,
            "provider_account_id": sample_entry.provider_account_id,
            "provider_customer_id": sample_entry.provider_customer_id,
            "metadata": sample_entry.metadata,
            "is_active": sample_entry.is_active,
            "created_at": sample_entry.created_at,
            "updated_at": sample_entry.updated_at,
        }

        mock_result.fetchone.return_value = mock_row
        mock_session.execute.return_value = mock_result

        # Should succeed without raising
        result = await sql_adapter.register(sample_entry, idempotency_key="test_key")

        # Verify the result
        assert result.id == sample_entry.id
        assert result.user_id == sample_entry.user_id
        assert result.provider == sample_entry.provider

        # Verify commit was called (not rollback)
        mock_session.commit.assert_called_once()
        mock_session.rollback.assert_not_called()

    @pytest.mark.asyncio
    async def test_row_mapping_used_for_safe_access(self, sql_adapter, sample_entry, mock_session):
        """Test that _row_to_entry uses row._mapping for safe access."""
        # Mock successful execution
        mock_result = MagicMock()
        mock_row = MagicMock()

        # Set up _mapping to return data
        test_data = {
            "external_id": sample_entry.id,
            "user_id": sample_entry.user_id,
            "provider": sample_entry.provider.value,
            "provider_account_id": sample_entry.provider_account_id,
            "provider_customer_id": sample_entry.provider_customer_id,
            "metadata": {"key": "value"},
            "is_active": True,
            "created_at": sample_entry.created_at,
            "updated_at": sample_entry.updated_at,
        }
        mock_row._mapping = test_data

        mock_result.fetchone.return_value = mock_row
        mock_session.execute.return_value = mock_result

        # Register should succeed and use _mapping
        result = await sql_adapter.register(sample_entry)

        # Verify _mapping was accessed (this would fail if direct attribute access was used)
        assert result.metadata == {"key": "value"}
        assert result.provider_account_id == test_data["provider_account_id"]
