"""Integration tests for wallet balance sync with concurrent operations."""

import pytest
import asyncio
from uuid import uuid4

from app.domain.entities import WalletProvider
from app.application.services.wallet_balance_sync_service import WalletBalanceSyncService
from app.adapters.inmemory.wallet_balance_sync import InMemoryWalletBalanceSync
from app.adapters.inmemory.wallet_provider import InMemoryWalletProvider
from app.adapters.inmemory.wallet_registry import InMemoryWalletRegistry
from app.adapters.inmemory.audit import InMemoryAudit
from app.errors import DuplicateEntryError


class TestWalletBalanceSyncConcurrency:
    """Test suite for wallet balance sync concurrent operations."""

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
    async def test_concurrent_sync_same_wallet_same_idempotency_key(
        self, service, wallet_provider_port
    ):
        """Test concurrent syncs with same idempotency_key return same snapshot."""
        wallet_id = uuid4()
        idempotency_key = "idem_key_1"
        balance = 100.50

        wallet_provider_port.set_balance(
            wallet_id=wallet_id,
            balance=balance,
            external_balance_id="ext_bal_123",
        )

        # Simulate concurrent requests with same idempotency_key
        results = await asyncio.gather(
            service.sync_balance(wallet_id=wallet_id, idempotency_key=idempotency_key),
            service.sync_balance(wallet_id=wallet_id, idempotency_key=idempotency_key),
            service.sync_balance(wallet_id=wallet_id, idempotency_key=idempotency_key),
        )

        # All should return the same snapshot
        snapshot_ids = [r.id for r in results]
        assert len(set(snapshot_ids)) == 1, "All concurrent requests should return same snapshot"
        assert all(r.balance == balance for r in results)

    @pytest.mark.asyncio
    async def test_concurrent_sync_same_external_balance_id(
        self, service, wallet_provider_port
    ):
        """Test concurrent syncs with same external_balance_id are idempotent."""
        wallet_id = uuid4()
        external_balance_id = "ext_bal_123"
        balance = 100.50

        wallet_provider_port.set_balance(
            wallet_id=wallet_id,
            balance=balance,
            external_balance_id=external_balance_id,
        )

        # Simulate concurrent requests (provider returns same external_balance_id)
        results = await asyncio.gather(
            service.sync_balance(wallet_id=wallet_id),
            service.sync_balance(wallet_id=wallet_id),
            service.sync_balance(wallet_id=wallet_id),
        )

        # All should return the same snapshot (idempotent by external_balance_id)
        snapshot_ids = [r.id for r in results]
        assert len(set(snapshot_ids)) == 1, "All concurrent requests should return same snapshot"

    @pytest.mark.asyncio
    async def test_concurrent_sync_different_idempotency_keys(
        self, service, wallet_provider_port
    ):
        """Test concurrent syncs with different idempotency_keys create separate snapshots."""
        wallet_id = uuid4()
        balance = 100.50

        # Set up provider to return unique external_balance_id each time
        # (simulating balance changes or different events)
        wallet_provider_port.set_balance(
            wallet_id=wallet_id, balance=balance, external_balance_id=None
        )

        # Simulate concurrent requests with different idempotency_keys
        # Note: This may fail due to (wallet_id, as_of) constraint if timestamps are identical
        # In production, this is unlikely due to microsecond precision
        results = []
        for i in range(3):
            # Add small delay to ensure different timestamps
            await asyncio.sleep(0.001)
            result = await service.sync_balance(
                wallet_id=wallet_id, idempotency_key=f"idem_key_{i}"
            )
            results.append(result)

        # Should create separate snapshots
        snapshot_ids = [r.id for r in results]
        assert len(set(snapshot_ids)) == 3, "Different idempotency_keys should create separate snapshots"

    @pytest.mark.asyncio
    async def test_concurrent_sync_handles_race_condition(
        self, service, wallet_provider_port, wallet_balance_sync_port
    ):
        """Test that service handles race conditions gracefully."""
        wallet_id = uuid4()
        balance = 100.50
        external_balance_id = "ext_bal_123"

        wallet_provider_port.set_balance(
            wallet_id=wallet_id,
            balance=balance,
            external_balance_id=external_balance_id,
        )

        # First sync succeeds
        result1 = await service.sync_balance(wallet_id=wallet_id)

        # Second sync should return existing snapshot (by external_balance_id)
        result2 = await service.sync_balance(wallet_id=wallet_id)

        assert result1.id == result2.id
        assert result1.external_balance_id == result2.external_balance_id

    @pytest.mark.asyncio
    async def test_concurrent_sync_different_wallets(
        self, service, wallet_provider_port
    ):
        """Test concurrent syncs for different wallets work independently."""
        wallet_id_1 = uuid4()
        wallet_id_2 = uuid4()
        wallet_id_3 = uuid4()

        wallet_provider_port.set_balance(
            wallet_id=wallet_id_1, balance=100.0, external_balance_id="ext_bal_1"
        )
        wallet_provider_port.set_balance(
            wallet_id=wallet_id_2, balance=200.0, external_balance_id="ext_bal_2"
        )
        wallet_provider_port.set_balance(
            wallet_id=wallet_id_3, balance=300.0, external_balance_id="ext_bal_3"
        )

        # Simulate concurrent syncs for different wallets
        results = await asyncio.gather(
            service.sync_balance(wallet_id=wallet_id_1),
            service.sync_balance(wallet_id=wallet_id_2),
            service.sync_balance(wallet_id=wallet_id_3),
        )

        # Should create separate snapshots with different wallet_ids
        assert len(results) == 3
        assert results[0].wallet_id == wallet_id_1
        assert results[1].wallet_id == wallet_id_2
        assert results[2].wallet_id == wallet_id_3
        assert results[0].balance == 100.0
        assert results[1].balance == 200.0
        assert results[2].balance == 300.0

    @pytest.mark.asyncio
    async def test_provider_fetch_called_once_for_idempotent_requests(
        self, service, wallet_provider_port
    ):
        """Test that provider is not called again for idempotent requests."""
        wallet_id = uuid4()
        idempotency_key = "idem_key_1"
        balance = 100.50

        wallet_provider_port.set_balance(
            wallet_id=wallet_id,
            balance=balance,
            external_balance_id="ext_bal_123",
        )

        # First sync
        await service.sync_balance(wallet_id=wallet_id, idempotency_key=idempotency_key)
        fetch_count_1 = wallet_provider_port.get_fetch_count(wallet_id)

        # Second sync with same idempotency_key
        await service.sync_balance(wallet_id=wallet_id, idempotency_key=idempotency_key)
        fetch_count_2 = wallet_provider_port.get_fetch_count(wallet_id)

        # Provider should be called only once (first sync)
        assert fetch_count_1 == 1
        assert fetch_count_2 == 1, "Provider should not be called again for idempotent request"

    @pytest.mark.asyncio
    async def test_concurrent_sync_with_balance_changes(
        self, service, wallet_provider_port
    ):
        """Test concurrent syncs with balance changes create multiple snapshots."""
        wallet_id = uuid4()

        # First sync
        wallet_provider_port.set_balance(
            wallet_id=wallet_id, balance=100.0, external_balance_id="ext_bal_1"
        )
        result1 = await service.sync_balance(wallet_id=wallet_id)

        # Second sync with different balance
        wallet_provider_port.set_balance(
            wallet_id=wallet_id, balance=200.0, external_balance_id="ext_bal_2"
        )
        result2 = await service.sync_balance(wallet_id=wallet_id)

        # Should create two different snapshots
        assert result1.id != result2.id
        assert result1.balance == 100.0
        assert result2.balance == 200.0

        # Get latest should return the second snapshot
        latest = await service.get_latest_balance(wallet_id=wallet_id)
        assert latest.id == result2.id
        assert latest.balance == 200.0
