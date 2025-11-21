"""Unit tests for SQL adapter duplicate entry translation.

This test verifies that the SQLWalletRegistry adapter properly translates
SQLAlchemy IntegrityError into the domain-level DuplicateEntryError.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from sqlalchemy.exc import IntegrityError
from sqlalchemy import MetaData

from app.domain.entities import WalletRegistryEntry, WalletProvider
from app.adapters.sql.wallet_registry import SQLWalletRegistry
from app.errors import DuplicateEntryError


class TestSQLAdapterDuplicateTranslation:
    """Test suite for SQL adapter IntegrityError translation."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock async session."""
        session = AsyncMock()
        return session

    @pytest.fixture
    def metadata(self):
        """Create a real metadata object for SQLAlchemy."""
        return MetaData()

    @pytest.fixture
    def sql_adapter(self, mock_session, metadata):
        """Create SQL wallet registry adapter with mocks."""
        return SQLWalletRegistry(session=mock_session, metadata=metadata)

    @pytest.mark.asyncio
    async def test_integrity_error_translated_to_duplicate_entry_error(
        self, sql_adapter, mock_session
    ):
        """Test that IntegrityError is translated to DuplicateEntryError."""
        # Create a test entry
        entry = WalletRegistryEntry(
            user_id=uuid4(),
            provider=WalletProvider.FINCRA,
            provider_account_id="wallet_123",
            is_active=True,
        )

        # Mock the session.execute to raise IntegrityError
        mock_session.execute.side_effect = IntegrityError(
            statement="INSERT INTO wallet_registry ...",
            params={},
            orig=Exception("duplicate key value violates unique constraint"),
        )

        # Verify that DuplicateEntryError is raised (not IntegrityError)
        with pytest.raises(DuplicateEntryError) as exc_info:
            await sql_adapter.register(entry=entry, idempotency_key="test_key")

        # Verify the error message
        assert "Duplicate wallet registration detected" in str(exc_info.value)

        # Verify that the original IntegrityError is preserved as the cause
        assert isinstance(exc_info.value.__cause__, IntegrityError)

        # Verify that session.rollback was called
        mock_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_integrity_error_on_duplicate_idempotency_key(
        self, sql_adapter, mock_session
    ):
        """Test IntegrityError translation for duplicate idempotency key."""
        entry = WalletRegistryEntry(
            user_id=uuid4(),
            provider=WalletProvider.PAYSTACK,
            provider_account_id="paystack_456",
            is_active=True,
        )

        # Simulate unique constraint violation on idempotency_key
        mock_session.execute.side_effect = IntegrityError(
            statement="INSERT INTO wallet_registry ...",
            params={},
            orig=Exception('duplicate key value violates unique constraint "wallet_registry_idempotency_key_key"'),
        )

        with pytest.raises(DuplicateEntryError) as exc_info:
            await sql_adapter.register(entry=entry, idempotency_key="duplicate_key")

        # Verify cause is preserved
        assert isinstance(exc_info.value.__cause__, IntegrityError)
        mock_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_integrity_error_on_duplicate_external_id(
        self, sql_adapter, mock_session
    ):
        """Test IntegrityError translation for duplicate external_id."""
        entry = WalletRegistryEntry(
            user_id=uuid4(),
            provider=WalletProvider.FLUTTERWAVE,
            provider_account_id="flutter_789",
            is_active=True,
        )

        # Simulate unique constraint violation on external_id
        mock_session.execute.side_effect = IntegrityError(
            statement="INSERT INTO wallet_registry ...",
            params={},
            orig=Exception('duplicate key value violates unique constraint "wallet_registry_external_id_key"'),
        )

        with pytest.raises(DuplicateEntryError):
            await sql_adapter.register(entry=entry)

        mock_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_successful_registration_does_not_raise_error(
        self, sql_adapter, mock_session
    ):
        """Test that successful registration does not raise any error."""
        entry = WalletRegistryEntry(
            id=uuid4(),
            user_id=uuid4(),
            provider=WalletProvider.FINCRA,
            provider_account_id="wallet_success",
            is_active=True,
        )

        # Mock successful execution
        mock_result = MagicMock()
        mock_row = MagicMock()
        mock_row._mapping = {
            "external_id": entry.id,
            "user_id": entry.user_id,
            "provider": entry.provider.value,
            "provider_account_id": entry.provider_account_id,
            "provider_customer_id": None,
            "metadata": {},
            "is_active": True,
            "created_at": entry.created_at,
            "updated_at": entry.updated_at,
        }
        mock_result.fetchone.return_value = mock_row
        mock_session.execute.return_value = mock_result

        # This should not raise any error
        result = await sql_adapter.register(entry=entry, idempotency_key="success_key")

        # Verify the result
        assert result.id == entry.id
        assert result.user_id == entry.user_id
        assert result.provider == entry.provider

        # Verify commit was called (not rollback)
        mock_session.commit.assert_called_once()
        mock_session.rollback.assert_not_called()
