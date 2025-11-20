"""Create link token use case."""

from uuid import UUID

from app.domain.entities import LinkToken, WalletProvider
from app.domain.services import LinkTokenService


class CreateLinkTokenUseCase:
    """Use case for creating a link token."""

    def __init__(self, link_token_service: LinkTokenService):
        """Initialize use case.

        Args:
            link_token_service: The link token service
        """
        self.link_token_service = link_token_service

    async def execute(self, user_id: UUID, provider: WalletProvider) -> LinkToken:
        """Execute the use case.

        Args:
            user_id: The user's unique identifier
            provider: The wallet provider

        Returns:
            The created link token
        """
        return await self.link_token_service.create_link_token(user_id, provider)
