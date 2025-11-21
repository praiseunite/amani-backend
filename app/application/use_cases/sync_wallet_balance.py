"""Sync wallet balance use case."""

from typing import Optional
from uuid import UUID

from app.domain.entities import WalletBalanceSnapshot
from app.application.services.wallet_balance_sync_service import WalletBalanceSyncService


class SyncWalletBalanceUseCase:
    """Use case for synchronizing wallet balance."""

    def __init__(self, wallet_balance_sync_service: WalletBalanceSyncService):
        """Initialize use case.

        Args:
            wallet_balance_sync_service: Service for wallet balance synchronization
        """
        self.wallet_balance_sync_service = wallet_balance_sync_service

    async def execute(
        self,
        wallet_id: UUID,
        idempotency_key: Optional[str] = None,
    ) -> WalletBalanceSnapshot:
        """Execute wallet balance sync.

        Args:
            wallet_id: The wallet's unique identifier
            idempotency_key: Optional idempotency key for duplicate prevention

        Returns:
            The wallet balance snapshot
        """
        return await self.wallet_balance_sync_service.sync_balance(
            wallet_id=wallet_id,
            idempotency_key=idempotency_key,
        )

    async def get_latest(self, wallet_id: UUID) -> Optional[WalletBalanceSnapshot]:
        """Get latest balance snapshot for a wallet.

        Args:
            wallet_id: The wallet's unique identifier

        Returns:
            Latest balance snapshot if found, None otherwise
        """
        return await self.wallet_balance_sync_service.get_latest_balance(wallet_id)
