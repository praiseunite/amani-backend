"""In-memory user repository implementation for testing."""

from typing import Dict, Optional
from uuid import UUID

from app.domain.entities import User
from app.ports.user_repository import UserRepositoryPort


class InMemoryUserRepository(UserRepositoryPort):
    """In-memory implementation of user repository."""

    def __init__(self):
        """Initialize in-memory storage."""
        self._users: Dict[UUID, User] = {}
        self._users_by_external_id: Dict[str, User] = {}

    async def find_by_id(self, user_id: UUID) -> Optional[User]:
        """Find user by ID.

        Args:
            user_id: The user's unique identifier

        Returns:
            User if found, None otherwise
        """
        return self._users.get(user_id)

    async def find_by_external_id(self, external_id: str) -> Optional[User]:
        """Find user by external ID.

        Args:
            external_id: The user's external identifier

        Returns:
            User if found, None otherwise
        """
        return self._users_by_external_id.get(external_id)

    async def save(self, user: User) -> User:
        """Save or update a user.

        Args:
            user: The user to save

        Returns:
            The saved user
        """
        self._users[user.id] = user
        if user.external_id:
            self._users_by_external_id[user.external_id] = user
        return user
