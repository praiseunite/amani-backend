"""In-memory link token repository implementation for testing."""

from datetime import datetime
from typing import Dict, Optional

from app.domain.entities import LinkToken
from app.ports.link_token import LinkTokenPort


class InMemoryLinkTokenRepository(LinkTokenPort):
    """In-memory implementation of link token repository."""

    def __init__(self):
        """Initialize in-memory storage."""
        self._tokens: Dict[str, LinkToken] = {}

    async def create(self, link_token: LinkToken) -> LinkToken:
        """Create a new link token.

        Args:
            link_token: The link token to create

        Returns:
            The created link token
        """
        self._tokens[link_token.token] = link_token
        return link_token

    async def find_by_token(self, token: str) -> Optional[LinkToken]:
        """Find a link token by its token string.

        Args:
            token: The token string to find

        Returns:
            The link token if found, None otherwise
        """
        return self._tokens.get(token)

    async def mark_consumed(self, link_token: LinkToken) -> LinkToken:
        """Mark a link token as consumed.

        Args:
            link_token: The link token to mark as consumed

        Returns:
            The updated link token
        """
        link_token.is_consumed = True
        link_token.consumed_at = datetime.utcnow()
        self._tokens[link_token.token] = link_token
        return link_token
