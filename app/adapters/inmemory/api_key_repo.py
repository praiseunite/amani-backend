"""In-memory API key repository implementation for testing."""

from typing import Dict, Optional

from app.ports.api_key import ApiKeyPort


class InMemoryApiKeyRepository(ApiKeyPort):
    """In-memory implementation of API key repository."""

    def __init__(self):
        """Initialize in-memory storage."""
        self._keys: Dict[str, str] = {}

    async def get_secret_by_key_id(self, key_id: str) -> Optional[str]:
        """Get API key secret by key ID.

        Args:
            key_id: The API key ID

        Returns:
            The API key secret if found, None otherwise
        """
        return self._keys.get(key_id)

    def add_key(self, key_id: str, secret: str) -> None:
        """Add an API key (for testing).

        Args:
            key_id: The API key ID
            secret: The API key secret
        """
        self._keys[key_id] = secret
