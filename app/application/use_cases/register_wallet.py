"""Register wallet use case."""

from uuid import UUID

from app.domain.entities import WalletRegistryEntry, WalletProvider
from app.domain.services import WalletRegistryService


class RegisterWalletUseCase:
    """Use case for registering a wallet."""

    def __init__(self, wallet_registry_service: WalletRegistryService):
        """Initialize use case.

        Args:
            wallet_registry_service: The wallet registry service
        """
        self.wallet_registry_service = wallet_registry_service

    async def execute(
        self,
        user_id: UUID,
        provider: WalletProvider,
        provider_account_id: str,
        provider_customer_id: str = None,
        metadata: dict = None,
    ) -> WalletRegistryEntry:
        """Execute the use case.

        Args:
            user_id: The user's unique identifier
            provider: The wallet provider
            provider_account_id: The provider account ID
            provider_customer_id: Optional provider customer ID
            metadata: Optional metadata

        Returns:
            The registered wallet entry
        """
        return await self.wallet_registry_service.register_wallet(
            user_id=user_id,
            provider=provider,
            provider_account_id=provider_account_id,
            provider_customer_id=provider_customer_id,
            metadata=metadata or {},
        )
