"""Wallet balance sync port - interface for wallet balance synchronization."""

from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from app.domain.entities import WalletBalanceSnapshot


class WalletBalanceSyncPort(ABC):
    """Port for wallet balance synchronization operations."""

    @abstractmethod
    async def sync_balance(
        self, wallet_id: UUID, idempotency_key: Optional[str] = None
    ) -> WalletBalanceSnapshot:
        """Synchronize wallet balance (idempotent).

        Fetches the current balance from the provider and creates a snapshot.
        If the snapshot already exists (by idempotency_key or external_balance_id),
        returns the existing snapshot.

        Args:
            wallet_id: The wallet's unique identifier
            idempotency_key: Optional idempotency key for duplicate prevention

        Returns:
            The wallet balance snapshot (new or existing)
        """
        pass

    @abstractmethod
    async def get_latest(self, wallet_id: UUID) -> Optional[WalletBalanceSnapshot]:
        """Get the latest balance snapshot for a wallet.

        Args:
            wallet_id: The wallet's unique identifier

        Returns:
            Latest balance snapshot if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_by_external_id(
        self, external_balance_id: str
    ) -> Optional[WalletBalanceSnapshot]:
        """Get balance snapshot by external provider event ID.

        Args:
            external_balance_id: The provider's balance event/snapshot ID

        Returns:
            Balance snapshot if found, None otherwise
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    async def get_by_idempotency_key(
        self, idempotency_key: str
    ) -> Optional[WalletBalanceSnapshot]:
        """Get snapshot by idempotency key.

        Args:
            idempotency_key: The idempotency key

        Returns:
            Balance snapshot if found, None otherwise
        """
        pass
