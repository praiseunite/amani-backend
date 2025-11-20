"""Link token port interface."""

from abc import ABC, abstractmethod
from typing import Optional
from app.domain.entities import LinkToken, WalletProvider


class LinkTokenPort(ABC):
    """Port interface for link token operations."""

    @abstractmethod
    async def create(self, user_id: str, provider: WalletProvider, token: str) -> LinkToken:
        """Create a new link token.

        Args:
            user_id: The user's unique identifier.
            provider: The wallet provider.
            token: The generated token string.

        Returns:
            The created LinkToken entity.
        """
        pass

    @abstractmethod
    async def consume(self, token_id: str) -> Optional[LinkToken]:
        """Mark a link token as consumed.

        Args:
            token_id: The link token's unique identifier.

        Returns:
            The updated LinkToken entity if found, None otherwise.
        """
        pass

    @abstractmethod
    async def find_by_token(self, token: str) -> Optional[LinkToken]:
        """Find a link token by its token string.

        Args:
            token: The token string to search for.

        Returns:
            The LinkToken entity if found, None otherwise.
        """
        pass
