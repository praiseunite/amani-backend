"""User repository port interface."""

from abc import ABC, abstractmethod
from typing import Optional
from app.domain.entities import User


class UserRepositoryPort(ABC):
    """Port interface for user repository operations."""

    @abstractmethod
    async def find_by_id(self, user_id: str) -> Optional[User]:
        """Find a user by their ID.

        Args:
            user_id: The user's unique identifier.

        Returns:
            The User entity if found, None otherwise.
        """
        pass

    @abstractmethod
    async def find_by_external_id(self, external_id: str) -> Optional[User]:
        """Find a user by their external ID.

        Args:
            external_id: The user's external identifier.

        Returns:
            The User entity if found, None otherwise.
        """
        pass

    @abstractmethod
    async def save(self, user: User) -> User:
        """Save a user entity.

        Args:
            user: The User entity to save.

        Returns:
            The saved User entity.
        """
        pass
