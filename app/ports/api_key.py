"""API key port - interface for API key operations."""

from abc import ABC, abstractmethod
from typing import Optional


class ApiKeyPort(ABC):
    """Port for API key operations."""

    @abstractmethod
    async def get_secret(self, key_id: str) -> Optional[str]:
        """Get the secret for an API key.

        Args:
            key_id: The API key identifier

        Returns:
            The secret if found, None otherwise
        """
        pass
