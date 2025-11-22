"""Bot link use case - consume token and link wallet provider."""

from typing import Optional

from app.domain.entities import LinkToken
from app.domain.services import LinkTokenService


class BotLinkService:
    """Service for linking bot wallets to users."""

    def __init__(
        self,
        link_token_service: LinkTokenService,
    ):
        """Initialize bot link service.

        Args:
            link_token_service: The link token service
        """
        self.link_token_service = link_token_service

    async def link_bot_wallet(self, token: str, provider_account_id: str) -> Optional[LinkToken]:
        """Link a bot wallet using a link token.

        Args:
            token: The link token string
            provider_account_id: The provider account ID

        Returns:
            The consumed link token if successful, None otherwise
        """
        # Consume the link token
        consumed_token = await self.link_token_service.consume_link_token(token)

        if consumed_token is None:
            return None

        return consumed_token


class BotLinkUseCase:
    """Use case for bot linking."""

    def __init__(self, bot_link_service: BotLinkService):
        """Initialize use case.

        Args:
            bot_link_service: The bot link service
        """
        self.bot_link_service = bot_link_service

    async def execute(self, token: str, provider_account_id: str) -> Optional[LinkToken]:
        """Execute the use case.

        Args:
            token: The link token string
            provider_account_id: The provider account ID

        Returns:
            The consumed link token if successful, None otherwise
        """
        return await self.bot_link_service.link_bot_wallet(token, provider_account_id)
