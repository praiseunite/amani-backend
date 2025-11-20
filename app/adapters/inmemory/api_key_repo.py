"""In-memory API key repository implementation for testing."""

from typing import Dict, Optional

from app.ports.api_key import ApiKeyPort


class InMemoryApiKeyRepository(ApiKeyPort):
    """In-memory implementation of API key repository."""

    def __init__(self):
        """Initialize in-memory storage."""
        self._keys: Dict[str, str] = {}

    async def get_secret(self, key_id: str) -> Optional[str]:
        """Get the secret for an API key.

        Args:
            key_id: The API key identifier

        Returns:
            The secret if found, None otherwise
        """
        return self._keys.get(key_id)

    def add_key(self, key_id: str, secret: str) -> None:
        """Add an API key (for testing).

        Args:
            key_id: The API key identifier
            secret: The secret for the key
        """
        self._keys[key_id] = secret
