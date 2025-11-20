"""User repository port - interface for user persistence."""

from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from app.domain.entities import User


class UserRepositoryPort(ABC):
    """Port for user repository operations."""

    @abstractmethod
    async def find_by_id(self, user_id: UUID) -> Optional[User]:
        """Find user by ID.

        Args:
            user_id: The user's unique identifier

        Returns:
            User if found, None otherwise
        """
        pass

    @abstractmethod
    async def find_by_external_id(self, external_id: str) -> Optional[User]:
        """Find user by external ID (e.g., Supabase auth ID).

        Args:
            external_id: The user's external identifier

        Returns:
            User if found, None otherwise
        """
        pass

    @abstractmethod
    async def save(self, user: User) -> User:
        """Save or update a user.

        Args:
            user: The user to save

        Returns:
            The saved user
        """
        pass
