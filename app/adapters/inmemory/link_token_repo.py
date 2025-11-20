"""In-memory implementation of LinkTokenPort for testing."""

from typing import Dict, Optional
import uuid
from datetime import datetime

from app.domain.entities import LinkToken, LinkTokenStatus, WalletProvider
from app.ports.link_token import LinkTokenPort


class InMemoryLinkTokenRepository(LinkTokenPort):
    """In-memory implementation of the link token repository."""

    def __init__(self):
        """Initialize the in-memory link token repository."""
        self._tokens: Dict[str, LinkToken] = {}
        self._token_string_index: Dict[str, str] = {}

    async def create(self, user_id: str, provider: WalletProvider, token: str) -> LinkToken:
        """Create a new link token.

        Args:
            user_id: The user's unique identifier.
            provider: The wallet provider.
            token: The generated token string.

        Returns:
            The created LinkToken entity.
        """
        token_id = str(uuid.uuid4())
        link_token = LinkToken(
            id=token_id,
            user_id=user_id,
            token=token,
            provider=provider,
            status=LinkTokenStatus.PENDING,
            created_at=datetime.utcnow(),
        )
        self._tokens[token_id] = link_token
        self._token_string_index[token] = token_id
        return link_token

    async def consume(self, token_id: str) -> Optional[LinkToken]:
        """Mark a link token as consumed.

        Args:
            token_id: The link token's unique identifier.

        Returns:
            The updated LinkToken entity if found, None otherwise.
        """
        token = self._tokens.get(token_id)
        if token:
            token.status = LinkTokenStatus.CONSUMED
            token.consumed_at = datetime.utcnow()
            return token
        return None

    async def find_by_token(self, token: str) -> Optional[LinkToken]:
        """Find a link token by its token string.

        Args:
            token: The token string to search for.

        Returns:
            The LinkToken entity if found, None otherwise.
        """
        token_id = self._token_string_index.get(token)
        if token_id:
            return self._tokens.get(token_id)
        return None
