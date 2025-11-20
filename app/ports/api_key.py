"""API key port - interface for API key operations."""

from abc import ABC, abstractmethod
from typing import Optional


class ApiKeyPort(ABC):
    """Port for API key operations."""

    @abstractmethod
    async def get_secret_by_key_id(self, key_id: str) -> Optional[str]:
        """Get API key secret by key ID.

        Args:
            key_id: The API key ID

        Returns:
            The API key secret if found, None otherwise
        """
        pass
