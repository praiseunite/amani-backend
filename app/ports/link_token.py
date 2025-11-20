"""Link token port - interface for link token operations."""

from abc import ABC, abstractmethod
from typing import Optional

from app.domain.entities import LinkToken


class LinkTokenPort(ABC):
    """Port for link token operations."""

    @abstractmethod
    async def create(self, link_token: LinkToken) -> LinkToken:
        """Create a new link token.

        Args:
            link_token: The link token to create

        Returns:
            The created link token
        """
        pass

    @abstractmethod
    async def find_by_token(self, token: str) -> Optional[LinkToken]:
        """Find a link token by its token string.

        Args:
            token: The token string to find

        Returns:
            The link token if found, None otherwise
        """
        pass

    @abstractmethod
    async def mark_consumed(self, link_token: LinkToken) -> LinkToken:
        """Mark a link token as consumed.

        Args:
            link_token: The link token to mark as consumed

        Returns:
            The updated link token
        """
        pass
