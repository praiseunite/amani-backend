"""Wallet Balance Sync Application Service.

Provides idempotent and concurrent-safe wallet balance synchronization.
Handles race conditions at the application layer.
"""

from typing import Optional
from uuid import UUID
from datetime import datetime

from app.domain.entities import WalletBalanceSnapshot, WalletProvider
from app.ports.wallet_balance_sync import WalletBalanceSyncPort
from app.ports.wallet_provider import WalletProviderPort
from app.ports.wallet_registry import WalletRegistryPort
from app.ports.audit import AuditPort
from app.errors import DuplicateEntryError


class WalletBalanceSyncService:
    """Application service for wallet balance synchronization with idempotent sync."""

    def __init__(
        self,
        wallet_balance_sync_port: WalletBalanceSyncPort,
        wallet_provider_port: WalletProviderPort,
        wallet_registry_port: WalletRegistryPort,
        audit_port: AuditPort,
    ):
        """Initialize wallet balance sync service.

        Args:
            wallet_balance_sync_port: Port for balance snapshot operations
            wallet_provider_port: Port for fetching balance from providers
            wallet_registry_port: Port for wallet registry operations
            audit_port: Port for audit operations
        """
        self.wallet_balance_sync_port = wallet_balance_sync_port
        self.wallet_provider_port = wallet_provider_port
        self.wallet_registry_port = wallet_registry_port
        self.audit_port = audit_port

    async def sync_balance(
        self,
        wallet_id: UUID,
        idempotency_key: Optional[str] = None,
    ) -> WalletBalanceSnapshot:
        """Synchronize wallet balance with idempotent behavior.

        This method ensures idempotent synchronization by:
        1. First checking for existing snapshot by idempotency_key
        2. Fetching current balance from provider
        3. Checking if snapshot with external_balance_id already exists
        4. Creating new snapshot only if balance has changed
        5. Handling race conditions by catching constraint violations

        Args:
            wallet_id: The wallet's unique identifier
            idempotency_key: Optional idempotency key for duplicate prevention

        Returns:
            The wallet balance snapshot (new or existing)
        """
        # Step 1: Check if already synced by idempotency_key
        if idempotency_key:
            existing = await self.wallet_balance_sync_port.get_by_idempotency_key(idempotency_key)
            if existing:
                return existing

        # Step 2: Get wallet information from registry
        # TODO: In production, fetch wallet details from wallet_registry using wallet_id
        # to get the actual provider and provider_account_id. For now, we use the latest
        # snapshot to infer provider, or default to FINCRA if no snapshots exist.
        # This is a known limitation that should be addressed when integrating with
        # the wallet registry lookup functionality.
        latest = await self.wallet_balance_sync_port.get_latest(wallet_id)

        # If no latest snapshot, we need wallet info - for this implementation
        # we'll use a default provider (in production this should be fetched from registry)
        provider = latest.provider if latest else WalletProvider.FINCRA
        provider_account_id = "default_account"  # TODO: Fetch from wallet_registry

        # Step 3: Fetch current balance from provider
        balance_data = await self.wallet_provider_port.fetch_balance(
            wallet_id=wallet_id,
            provider=provider,
            provider_account_id=provider_account_id,
        )

        # Step 4: Check if snapshot with this external_balance_id exists
        external_balance_id = balance_data.get("external_balance_id")
        if external_balance_id:
            existing = await self.wallet_balance_sync_port.get_by_external_id(external_balance_id)
            if existing:
                return existing

        # Step 5: Check if balance has changed from latest snapshot
        if latest:
            balance_changed = (
                latest.balance != balance_data["balance"]
                or latest.currency != balance_data["currency"]
            )
            if not balance_changed and not idempotency_key:
                # Balance hasn't changed, return latest snapshot
                return latest

        # Step 6: Create new snapshot
        snapshot = WalletBalanceSnapshot(
            wallet_id=wallet_id,
            provider=provider,
            balance=balance_data["balance"],
            currency=balance_data["currency"],
            external_balance_id=external_balance_id,
            as_of=datetime.utcnow(),
            metadata=balance_data.get("metadata", {}),
        )

        try:
            # Try to save snapshot - may fail due to race condition
            saved = await self.wallet_balance_sync_port.save_snapshot(
                snapshot=snapshot,
                idempotency_key=idempotency_key,
            )

            # Record audit event for new snapshot
            # TODO: Consider adding user_id parameter to sync_balance method
            # to properly track which user initiated the sync. For now, using
            # wallet_id as a placeholder to maintain audit trail functionality.
            await self.audit_port.record(
                user_id=wallet_id,  # Using wallet_id as placeholder; should be actual user_id
                action="sync_balance",
                resource_type="wallet_balance_snapshot",
                resource_id=str(saved.id),
                details={
                    "wallet_id": str(wallet_id),
                    "provider": provider.value,
                    "balance": balance_data["balance"],
                    "currency": balance_data["currency"],
                    "external_balance_id": external_balance_id,
                    "idempotency_key": idempotency_key,
                },
            )

            return saved

        except DuplicateEntryError:
            # Handle race condition - another request created the snapshot
            # Fetch and return the existing snapshot

            # Try fetching by idempotency_key first
            if idempotency_key:
                existing = await self.wallet_balance_sync_port.get_by_idempotency_key(
                    idempotency_key
                )
                if existing:
                    return existing

            # Try fetching by external_balance_id
            if external_balance_id:
                existing = await self.wallet_balance_sync_port.get_by_external_id(
                    external_balance_id
                )
                if existing:
                    return existing

            # Fall back to latest snapshot
            existing = await self.wallet_balance_sync_port.get_latest(wallet_id)
            if existing:
                return existing

            # If we couldn't resolve the race, re-raise the exception
            raise

    async def get_latest_balance(self, wallet_id: UUID) -> Optional[WalletBalanceSnapshot]:
        """Get the latest balance snapshot for a wallet.

        Args:
            wallet_id: The wallet's unique identifier

        Returns:
            Latest balance snapshot if found, None otherwise
        """
        return await self.wallet_balance_sync_port.get_latest(wallet_id)
