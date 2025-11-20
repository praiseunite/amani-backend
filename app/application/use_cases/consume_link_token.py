"""Consume link token use case."""

from typing import Optional

from app.domain.entities import WalletRegistryEntry
from app.domain.services import LinkTokenService
from app.ports.wallet_registry import WalletRegistryPort
from app.ports.audit import AuditPort


class ConsumeLinkTokenUseCase:
    """Use case for consuming a link token and linking a provider account."""

    def __init__(
        self,
        link_token_service: LinkTokenService,
        wallet_registry_port: WalletRegistryPort,
        audit_port: AuditPort,
    ):
        """Initialize use case.

        Args:
            link_token_service: The link token service
            wallet_registry_port: The wallet registry port
            audit_port: The audit port
        """
        self.link_token_service = link_token_service
        self.wallet_registry_port = wallet_registry_port
        self.audit_port = audit_port

    async def execute(
        self, token: str, provider_account_id: str, provider_customer_id: Optional[str] = None
    ) -> Optional[WalletRegistryEntry]:
        """Execute the use case.

        Args:
            token: The link token string
            provider_account_id: The provider's account ID
            provider_customer_id: Optional provider's customer ID

        Returns:
            The wallet registry entry if token is valid, None otherwise
        """
        # Consume the link token
        consumed_token = await self.link_token_service.consume_link_token(token)

        if consumed_token is None:
            return None

        # Register the wallet
        wallet_entry = WalletRegistryEntry(
            user_id=consumed_token.user_id,
            provider=consumed_token.provider,
            provider_account_id=provider_account_id,
            provider_customer_id=provider_customer_id,
            is_active=True,
        )

        saved_wallet = await self.wallet_registry_port.register(wallet_entry)

        # Audit the wallet linkage
        await self.audit_port.record(
            user_id=consumed_token.user_id,
            action="link_wallet",
            resource_type="wallet_registry",
            resource_id=str(saved_wallet.id),
            details={
                "provider": consumed_token.provider.value,
                "provider_account_id": provider_account_id,
                "link_token_id": str(consumed_token.id),
            },
        )

        return saved_wallet
