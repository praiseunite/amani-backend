"""Register wallet use case."""

from typing import Optional
from uuid import UUID

from app.domain.entities import WalletRegistryEntry, WalletProvider
from app.ports.wallet_registry import WalletRegistryPort
from app.ports.audit import AuditPort


class RegisterWalletUseCase:
    """Use case for registering a wallet (idempotent)."""

    def __init__(self, wallet_registry_port: WalletRegistryPort, audit_port: AuditPort):
        """Initialize use case.

        Args:
            wallet_registry_port: The wallet registry port
            audit_port: The audit port
        """
        self.wallet_registry_port = wallet_registry_port
        self.audit_port = audit_port

    async def execute(
        self,
        user_id: UUID,
        provider: WalletProvider,
        provider_account_id: str,
        provider_customer_id: Optional[str] = None,
    ) -> WalletRegistryEntry:
        """Execute the use case (idempotent).

        Args:
            user_id: The user's unique identifier
            provider: The wallet provider
            provider_account_id: The provider's account ID
            provider_customer_id: Optional provider's customer ID

        Returns:
            The wallet registry entry (existing or newly created)
        """
        # Check if wallet already exists
        existing = await self.wallet_registry_port.get_by_provider(user_id, provider)

        if existing:
            # Return existing wallet (idempotent behavior)
            return existing

        # Create new wallet entry
        wallet_entry = WalletRegistryEntry(
            user_id=user_id,
            provider=provider,
            provider_account_id=provider_account_id,
            provider_customer_id=provider_customer_id,
            is_active=True,
        )

        saved_wallet = await self.wallet_registry_port.register(wallet_entry)

        # Audit the wallet registration
        await self.audit_port.record(
            user_id=user_id,
            action="register_wallet",
            resource_type="wallet_registry",
            resource_id=str(saved_wallet.id),
            details={
                "provider": provider.value,
                "provider_account_id": provider_account_id,
            },
        )

        return saved_wallet
