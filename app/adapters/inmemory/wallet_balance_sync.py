"""In-memory wallet balance sync implementation for testing."""

from typing import Dict, List, Optional
from uuid import UUID
from datetime import datetime

from app.domain.entities import WalletBalanceSnapshot
from app.ports.wallet_balance_sync import WalletBalanceSyncPort
from app.errors import DuplicateEntryError


class InMemoryWalletBalanceSync(WalletBalanceSyncPort):
    """In-memory implementation of wallet balance sync."""

    def __init__(self):
        """Initialize in-memory storage."""
        self._snapshots: List[WalletBalanceSnapshot] = []
        self._idempotency_keys: Dict[str, WalletBalanceSnapshot] = {}
        self._external_ids: Dict[str, WalletBalanceSnapshot] = {}

    async def sync_balance(
        self, wallet_id: UUID, idempotency_key: Optional[str] = None
    ) -> WalletBalanceSnapshot:
        """Synchronize wallet balance (idempotent).

        Note: This method is not typically called directly in tests.
        Use save_snapshot instead.

        Args:
            wallet_id: The wallet's unique identifier
            idempotency_key: Optional idempotency key for duplicate prevention

        Returns:
            The wallet balance snapshot
        """
        # For in-memory testing, this method delegates to save_snapshot
        # In production, this would also fetch from provider
        raise NotImplementedError("Use save_snapshot for in-memory testing")

    async def get_latest(self, wallet_id: UUID) -> Optional[WalletBalanceSnapshot]:
        """Get the latest balance snapshot for a wallet.

        Args:
            wallet_id: The wallet's unique identifier

        Returns:
            Latest balance snapshot if found, None otherwise
        """
        wallet_snapshots = [s for s in self._snapshots if s.wallet_id == wallet_id]
        if not wallet_snapshots:
            return None
        # Return the most recent snapshot
        return max(wallet_snapshots, key=lambda s: s.as_of)

    async def get_by_external_id(
        self, external_balance_id: str
    ) -> Optional[WalletBalanceSnapshot]:
        """Get balance snapshot by external provider event ID.

        Args:
            external_balance_id: The provider's balance event/snapshot ID

        Returns:
            Balance snapshot if found, None otherwise
        """
        return self._external_ids.get(external_balance_id)

    async def save_snapshot(
        self, snapshot: WalletBalanceSnapshot, idempotency_key: Optional[str] = None
    ) -> WalletBalanceSnapshot:
        """Save a balance snapshot.

        Args:
            snapshot: The balance snapshot to save
            idempotency_key: Optional idempotency key for duplicate prevention

        Returns:
            The saved snapshot

        Raises:
            DuplicateEntryError: On unique constraint violations
        """
        # Check for duplicate idempotency_key
        if idempotency_key and idempotency_key in self._idempotency_keys:
            raise DuplicateEntryError("Duplicate idempotency key")

        # Check for duplicate external_balance_id
        if (
            snapshot.external_balance_id
            and snapshot.external_balance_id in self._external_ids
        ):
            raise DuplicateEntryError("Duplicate external balance ID")

        # Check for duplicate (wallet_id, as_of) - unique constraint
        for existing in self._snapshots:
            if (
                existing.wallet_id == snapshot.wallet_id
                and existing.as_of == snapshot.as_of
            ):
                raise DuplicateEntryError("Duplicate wallet_id and as_of timestamp")

        # Save snapshot
        self._snapshots.append(snapshot)
        if idempotency_key:
            self._idempotency_keys[idempotency_key] = snapshot
        if snapshot.external_balance_id:
            self._external_ids[snapshot.external_balance_id] = snapshot
        return snapshot

    async def get_by_idempotency_key(
        self, idempotency_key: str
    ) -> Optional[WalletBalanceSnapshot]:
        """Get snapshot by idempotency key.

        Args:
            idempotency_key: The idempotency key

        Returns:
            Balance snapshot if found, None otherwise
        """
        return self._idempotency_keys.get(idempotency_key)
