"""Wallet Registry Application Service.

Provides idempotent and concurrent-safe wallet registration.
Handles race conditions at the application layer.
"""

from typing import Optional
from uuid import UUID

from app.domain.entities import WalletRegistryEntry, WalletProvider
from app.ports.wallet_registry import WalletRegistryPort
from app.ports.audit import AuditPort
from app.errors import DuplicateEntryError


class WalletRegistryService:
    """Application service for wallet registry with idempotent registration."""

    def __init__(
        self,
        wallet_registry_port: WalletRegistryPort,
        audit_port: AuditPort,
    ):
        """Initialize wallet registry service.

        Args:
            wallet_registry_port: Port for wallet registry operations
            audit_port: Port for audit operations
        """
        self.wallet_registry_port = wallet_registry_port
        self.audit_port = audit_port

    async def register(
        self,
        user_id: UUID,
        provider: WalletProvider,
        provider_wallet_id: str,
        idempotency_key: Optional[str] = None,
        provider_customer_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> WalletRegistryEntry:
        """Register a wallet with idempotent behavior.

        This method ensures idempotent registration by:
        1. First checking for existing registration by idempotency_key
        2. Then checking by provider + provider_wallet_id
        3. Handling race conditions by catching constraint violations and fetching the existing row

        Args:
            user_id: The user's unique identifier
            provider: The wallet provider
            provider_wallet_id: The provider's wallet/account ID
            idempotency_key: Optional idempotency key for duplicate prevention
            provider_customer_id: Optional provider customer ID
            metadata: Optional metadata dictionary

        Returns:
            The registered wallet entry (new or existing)
        """
        # Step 1: Check if already registered by idempotency_key
        if idempotency_key:
            existing = await self.wallet_registry_port.get_by_idempotency_key(idempotency_key)
            if existing:
                return existing

        # Step 2: Check if already registered by provider + provider_wallet_id
        existing = await self.wallet_registry_port.get_by_provider_wallet(
            user_id=user_id,
            provider=provider,
            provider_wallet_id=provider_wallet_id,
        )
        if existing:
            return existing

        # Step 3: Attempt to create new entry
        entry = WalletRegistryEntry(
            user_id=user_id,
            provider=provider,
            provider_account_id=provider_wallet_id,
            provider_customer_id=provider_customer_id,
            metadata=metadata or {},
            is_active=True,
        )

        try:
            # Try to register - may fail due to race condition
            registered = await self.wallet_registry_port.register(
                entry=entry,
                idempotency_key=idempotency_key,
            )

            # Record audit event for new registration
            await self.audit_port.record(
                user_id=user_id,
                action="register_wallet",
                resource_type="wallet_registry",
                resource_id=str(registered.id),
                details={
                    "provider": provider.value,
                    "provider_wallet_id": provider_wallet_id,
                    "idempotency_key": idempotency_key,
                },
            )

            return registered

        except DuplicateEntryError:
            # Handle race condition - another request created the entry
            # Fetch and return the existing entry
            # Try fetching by idempotency_key first
            if idempotency_key:
                existing = await self.wallet_registry_port.get_by_idempotency_key(idempotency_key)
                if existing:
                    return existing

            # Fall back to provider + provider_wallet_id
            existing = await self.wallet_registry_port.get_by_provider_wallet(
                user_id=user_id,
                provider=provider,
                provider_wallet_id=provider_wallet_id,
            )
            if existing:
                return existing

            # If we couldn't resolve the race, re-raise the exception
            raise
