"""Use case for creating a link token.

This module provides the application-level orchestration for link token creation.
"""

from app.domain.entities import LinkToken, WalletProvider
from app.domain.services import LinkTokenService


class CreateLinkTokenUseCase:
    """Use case for creating a link token."""

    def __init__(self, link_token_service: LinkTokenService):
        """Initialize the use case.

        Args:
            link_token_service: The link token service.
        """
        self.link_token_service = link_token_service

    async def execute(self, user_id: str, provider: WalletProvider) -> LinkToken:
        """Execute the use case to create a link token.

        Args:
            user_id: The user's unique identifier.
            provider: The wallet provider.

        Returns:
            The created LinkToken entity.

        Raises:
            ValueError: If the user is not found or not authorized.
        """
        return await self.link_token_service.create_link_token(user_id, provider)
