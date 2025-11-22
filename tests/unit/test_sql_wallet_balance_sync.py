"""Unit tests for SQL wallet balance sync adapter."""

import pytest
from datetime import datetime
from decimal import Decimal
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

from sqlalchemy import MetaData
from sqlalchemy.exc import IntegrityError

from app.adapters.sql.wallet_balance_sync import SQLWalletBalanceSync
from app.domain.entities import WalletBalanceSnapshot, WalletProvider
from app.errors import DuplicateEntryError


@pytest.mark.unit
class TestSQLWalletBalanceSync:
    """Test SQL wallet balance sync adapter."""

    def setup_method(self):
        """Setup test fixtures."""
        self.session = AsyncMock()
        self.metadata = MetaData()
        self.adapter = SQLWalletBalanceSync(self.session, self.metadata)

    @pytest.mark.asyncio
    async def test_get_latest_found(self):
        """Test getting latest snapshot when one exists."""
        wallet_id = uuid4()
        
        # Mock database result
        mock_row = MagicMock()
        mock_row._mapping = {
            "id": uuid4(),
            "wallet_id": wallet_id,
            "provider": "fincra",
            "balance": Decimal("1000.00"),
            "currency": "NGN",
            "external_balance_id": "ext_123",
            "as_of": datetime.utcnow(),
            "metadata": {},
            "created_at": datetime.utcnow()
        }
        
        mock_result = MagicMock()
        mock_result.fetchone.return_value = mock_row
        self.session.execute.return_value = mock_result
        
        # Get latest snapshot
        snapshot = await self.adapter.get_latest(wallet_id)
        
        # Verify
        assert snapshot is not None
        assert snapshot.wallet_id == wallet_id
        assert snapshot.provider == WalletProvider.FINCRA
        assert snapshot.balance == 1000.00
        assert snapshot.currency == "NGN"

    @pytest.mark.asyncio
    async def test_get_latest_not_found(self):
        """Test getting latest snapshot when none exists."""
        wallet_id = uuid4()
        
        # Mock empty result
        mock_result = MagicMock()
        mock_result.fetchone.return_value = None
        self.session.execute.return_value = mock_result
        
        # Get latest snapshot
        snapshot = await self.adapter.get_latest(wallet_id)
        
        # Verify
        assert snapshot is None

    @pytest.mark.asyncio
    async def test_get_by_external_id_found(self):
        """Test getting snapshot by external ID when found."""
        external_id = "ext_123"
        
        # Mock database result
        mock_row = MagicMock()
        mock_row._mapping = {
            "id": uuid4(),
            "wallet_id": uuid4(),
            "provider": "fincra",
            "balance": Decimal("1000.00"),
            "currency": "NGN",
            "external_balance_id": external_id,
            "as_of": datetime.utcnow(),
            "metadata": {},
            "created_at": datetime.utcnow()
        }
        
        mock_result = MagicMock()
        mock_result.fetchone.return_value = mock_row
        self.session.execute.return_value = mock_result
        
        # Get snapshot
        snapshot = await self.adapter.get_by_external_id(external_id)
        
        # Verify
        assert snapshot is not None
        assert snapshot.external_balance_id == external_id

    @pytest.mark.asyncio
    async def test_get_by_external_id_not_found(self):
        """Test getting snapshot by external ID when not found."""
        external_id = "ext_999"
        
        # Mock empty result
        mock_result = MagicMock()
        mock_result.fetchone.return_value = None
        self.session.execute.return_value = mock_result
        
        # Get snapshot
        snapshot = await self.adapter.get_by_external_id(external_id)
        
        # Verify
        assert snapshot is None

    @pytest.mark.asyncio
    async def test_save_snapshot_success(self):
        """Test saving a snapshot successfully."""
        snapshot = WalletBalanceSnapshot(
            id=uuid4(),
            wallet_id=uuid4(),
            provider=WalletProvider.FINCRA,
            balance=1000.00,
            currency="NGN",
            external_balance_id="ext_123",
            as_of=datetime.utcnow(),
            metadata={}
        )
        
        # Mock database result
        mock_row = MagicMock()
        mock_row._mapping = {
            "id": snapshot.id,
            "wallet_id": snapshot.wallet_id,
            "provider": "fincra",
            "balance": Decimal(str(snapshot.balance)),
            "currency": snapshot.currency,
            "external_balance_id": snapshot.external_balance_id,
            "as_of": snapshot.as_of,
            "metadata": snapshot.metadata,
            "created_at": datetime.utcnow()
        }
        
        mock_result = MagicMock()
        mock_result.fetchone.return_value = mock_row
        self.session.execute.return_value = mock_result
        self.session.commit = AsyncMock()
        
        # Save snapshot
        saved = await self.adapter.save_snapshot(snapshot, idempotency_key="test_key")
        
        # Verify
        assert saved is not None
        assert saved.id == snapshot.id
        assert saved.wallet_id == snapshot.wallet_id
        self.session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_snapshot_duplicate_error(self):
        """Test saving a duplicate snapshot raises DuplicateEntryError."""
        snapshot = WalletBalanceSnapshot(
            id=uuid4(),
            wallet_id=uuid4(),
            provider=WalletProvider.FINCRA,
            balance=1000.00,
            currency="NGN",
            external_balance_id="ext_123",
            as_of=datetime.utcnow(),
            metadata={}
        )
        
        # Mock IntegrityError
        self.session.execute.side_effect = IntegrityError("statement", "params", "orig")
        self.session.rollback = AsyncMock()
        
        # Save snapshot should raise DuplicateEntryError
        with pytest.raises(DuplicateEntryError):
            await self.adapter.save_snapshot(snapshot, idempotency_key="test_key")
        
        # Verify rollback was called
        self.session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_idempotency_key_found(self):
        """Test getting snapshot by idempotency key when found."""
        idempotency_key = "test_key_123"
        
        # Mock database result
        mock_row = MagicMock()
        mock_row._mapping = {
            "id": uuid4(),
            "wallet_id": uuid4(),
            "provider": "fincra",
            "balance": Decimal("1000.00"),
            "currency": "NGN",
            "external_balance_id": "ext_123",
            "as_of": datetime.utcnow(),
            "metadata": {},
            "created_at": datetime.utcnow()
        }
        
        mock_result = MagicMock()
        mock_result.fetchone.return_value = mock_row
        self.session.execute.return_value = mock_result
        
        # Get snapshot
        snapshot = await self.adapter.get_by_idempotency_key(idempotency_key)
        
        # Verify
        assert snapshot is not None

    @pytest.mark.asyncio
    async def test_get_by_idempotency_key_not_found(self):
        """Test getting snapshot by idempotency key when not found."""
        idempotency_key = "test_key_999"
        
        # Mock empty result
        mock_result = MagicMock()
        mock_result.fetchone.return_value = None
        self.session.execute.return_value = mock_result
        
        # Get snapshot
        snapshot = await self.adapter.get_by_idempotency_key(idempotency_key)
        
        # Verify
        assert snapshot is None
