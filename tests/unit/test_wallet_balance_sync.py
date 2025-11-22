"""Unit tests for wallet balance sync service."""

import pytest
from uuid import uuid4
from datetime import datetime, timedelta

from app.domain.entities import WalletProvider, WalletBalanceSnapshot
from app.application.services.wallet_balance_sync_service import WalletBalanceSyncService
from app.adapters.inmemory.wallet_balance_sync import InMemoryWalletBalanceSync
from app.adapters.inmemory.wallet_provider import InMemoryWalletProvider
from app.adapters.inmemory.wallet_registry import InMemoryWalletRegistry
from app.adapters.inmemory.audit import InMemoryAudit


class TestWalletBalanceSyncService:
    """Test suite for wallet balance sync service."""

    @pytest.fixture
    def wallet_balance_sync_port(self):
        """Create in-memory wallet balance sync port."""
        return InMemoryWalletBalanceSync()

    @pytest.fixture
    def wallet_provider_port(self):
        """Create in-memory wallet provider port."""
        return InMemoryWalletProvider()

    @pytest.fixture
    def wallet_registry_port(self):
        """Create in-memory wallet registry port."""
        return InMemoryWalletRegistry()

    @pytest.fixture
    def audit_port(self):
        """Create in-memory audit port."""
        return InMemoryAudit()

    @pytest.fixture
    def service(
        self,
        wallet_balance_sync_port,
        wallet_provider_port,
        wallet_registry_port,
        audit_port,
    ):
        """Create wallet balance sync service."""
        return WalletBalanceSyncService(
            wallet_balance_sync_port=wallet_balance_sync_port,
            wallet_provider_port=wallet_provider_port,
            wallet_registry_port=wallet_registry_port,
            audit_port=audit_port,
        )

    @pytest.mark.asyncio
    async def test_sync_new_balance(self, service, wallet_provider_port):
        """Test syncing a new balance."""
        wallet_id = uuid4()
        balance = 100.50
        currency = "USD"
        external_balance_id = "ext_bal_123"

        # Set up mock provider
        wallet_provider_port.set_balance(
            wallet_id=wallet_id,
            balance=balance,
            currency=currency,
            external_balance_id=external_balance_id,
        )

        # Sync balance
        result = await service.sync_balance(wallet_id=wallet_id)

        assert result is not None
        assert result.wallet_id == wallet_id
        assert result.balance == balance
        assert result.currency == currency
        assert result.external_balance_id == external_balance_id
        assert result.provider == WalletProvider.FINCRA

    @pytest.mark.asyncio
    async def test_sync_idempotent_same_idempotency_key(self, service, wallet_provider_port):
        """Test that syncing with same idempotency_key returns existing snapshot."""
        wallet_id = uuid4()
        idempotency_key = "idem_key_1"
        balance = 100.50

        wallet_provider_port.set_balance(
            wallet_id=wallet_id,
            balance=balance,
            external_balance_id="ext_bal_123",
        )

        # First sync
        result1 = await service.sync_balance(wallet_id=wallet_id, idempotency_key=idempotency_key)

        # Second sync with same idempotency_key
        result2 = await service.sync_balance(wallet_id=wallet_id, idempotency_key=idempotency_key)

        # Should return the same snapshot
        assert result1.id == result2.id
        assert result1.wallet_id == result2.wallet_id
        assert result1.balance == result2.balance

    @pytest.mark.asyncio
    async def test_sync_idempotent_same_external_balance_id(self, service, wallet_provider_port):
        """Test that syncing returns existing snapshot if external_balance_id matches."""
        wallet_id = uuid4()
        external_balance_id = "ext_bal_123"
        balance = 100.50

        wallet_provider_port.set_balance(
            wallet_id=wallet_id,
            balance=balance,
            external_balance_id=external_balance_id,
        )

        # First sync
        result1 = await service.sync_balance(wallet_id=wallet_id)

        # Second sync (provider returns same external_balance_id)
        result2 = await service.sync_balance(wallet_id=wallet_id)

        # Should return the same snapshot (idempotent by external_balance_id)
        assert result1.id == result2.id

    @pytest.mark.asyncio
    async def test_sync_creates_new_snapshot_on_balance_change(self, service, wallet_provider_port):
        """Test that sync creates new snapshot when balance changes."""
        wallet_id = uuid4()
        balance1 = 100.50
        balance2 = 200.75

        # First sync with balance1
        wallet_provider_port.set_balance(
            wallet_id=wallet_id,
            balance=balance1,
            external_balance_id="ext_bal_1",
        )
        result1 = await service.sync_balance(wallet_id=wallet_id)

        # Second sync with balance2 (changed)
        wallet_provider_port.set_balance(
            wallet_id=wallet_id,
            balance=balance2,
            external_balance_id="ext_bal_2",
        )
        result2 = await service.sync_balance(wallet_id=wallet_id)

        # Should be different snapshots
        assert result1.id != result2.id
        assert result1.balance == balance1
        assert result2.balance == balance2

    @pytest.mark.asyncio
    async def test_sync_no_new_snapshot_if_balance_unchanged(self, service, wallet_provider_port):
        """Test that sync doesn't create new snapshot if balance hasn't changed."""
        wallet_id = uuid4()
        balance = 100.50

        # First sync
        wallet_provider_port.set_balance(
            wallet_id=wallet_id,
            balance=balance,
            external_balance_id="ext_bal_1",
        )
        result1 = await service.sync_balance(wallet_id=wallet_id)

        # Second sync with same balance (no external_balance_id to force new snapshot)
        wallet_provider_port.set_balance(
            wallet_id=wallet_id,
            balance=balance,
            external_balance_id=None,  # No external ID
        )
        result2 = await service.sync_balance(wallet_id=wallet_id)

        # Should return the same snapshot (balance unchanged)
        assert result1.id == result2.id

    @pytest.mark.asyncio
    async def test_get_latest_balance(self, service, wallet_provider_port):
        """Test getting latest balance snapshot."""
        wallet_id = uuid4()
        balance1 = 100.50
        balance2 = 200.75

        # Sync twice
        wallet_provider_port.set_balance(
            wallet_id=wallet_id,
            balance=balance1,
            external_balance_id="ext_bal_1",
        )
        await service.sync_balance(wallet_id=wallet_id)

        wallet_provider_port.set_balance(
            wallet_id=wallet_id,
            balance=balance2,
            external_balance_id="ext_bal_2",
        )
        result2 = await service.sync_balance(wallet_id=wallet_id)

        # Get latest should return the second snapshot
        latest = await service.get_latest_balance(wallet_id=wallet_id)
        assert latest is not None
        assert latest.id == result2.id
        assert latest.balance == balance2

    @pytest.mark.asyncio
    async def test_get_latest_balance_returns_none_if_no_snapshots(self, service):
        """Test that get_latest_balance returns None if no snapshots exist."""
        wallet_id = uuid4()
        latest = await service.get_latest_balance(wallet_id=wallet_id)
        assert latest is None

    @pytest.mark.asyncio
    async def test_sync_with_metadata(self, service, wallet_provider_port):
        """Test syncing balance with metadata."""
        wallet_id = uuid4()
        metadata = {"tier": "premium", "verified": True}

        wallet_provider_port.set_balance(
            wallet_id=wallet_id,
            balance=100.50,
            external_balance_id="ext_bal_123",
            metadata=metadata,
        )

        result = await service.sync_balance(wallet_id=wallet_id)
        assert result.metadata == metadata

    @pytest.mark.asyncio
    async def test_audit_events_recorded(self, service, wallet_provider_port, audit_port):
        """Test that audit events are recorded for new syncs."""
        wallet_id = uuid4()
        balance = 100.50
        external_balance_id = "ext_bal_123"

        wallet_provider_port.set_balance(
            wallet_id=wallet_id,
            balance=balance,
            external_balance_id=external_balance_id,
        )

        # Sync balance
        await service.sync_balance(wallet_id=wallet_id)

        # Check audit events
        events = audit_port.get_events()
        assert len(events) == 1
        assert events[0]["action"] == "sync_balance"
        assert events[0]["resource_type"] == "wallet_balance_snapshot"
        assert events[0]["details"]["wallet_id"] == str(wallet_id)
        assert events[0]["details"]["balance"] == balance
        assert events[0]["details"]["external_balance_id"] == external_balance_id

    @pytest.mark.asyncio
    async def test_no_duplicate_audit_for_idempotent_request(
        self, service, wallet_provider_port, audit_port
    ):
        """Test that no duplicate audit events for idempotent requests."""
        wallet_id = uuid4()
        idempotency_key = "idem_key_1"

        wallet_provider_port.set_balance(
            wallet_id=wallet_id,
            balance=100.50,
            external_balance_id="ext_bal_123",
        )

        # First sync
        await service.sync_balance(wallet_id=wallet_id, idempotency_key=idempotency_key)

        # Second sync (idempotent)
        await service.sync_balance(wallet_id=wallet_id, idempotency_key=idempotency_key)

        # Should only have one audit event (from first sync)
        events = audit_port.get_events()
        assert len(events) == 1
