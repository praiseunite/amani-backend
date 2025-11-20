"""In-memory implementation of UserRepositoryPort for testing."""

from typing import Dict, Optional
from app.domain.entities import User
from app.ports.user_repository import UserRepositoryPort


class InMemoryUserRepository(UserRepositoryPort):
    """In-memory implementation of the user repository."""

    def __init__(self):
        """Initialize the in-memory user repository."""
        self._users: Dict[str, User] = {}
        self._external_id_index: Dict[str, str] = {}

    async def find_by_id(self, user_id: str) -> Optional[User]:
        """Find a user by their ID.

        Args:
            user_id: The user's unique identifier.

        Returns:
            The User entity if found, None otherwise.
        """
        return self._users.get(user_id)

    async def find_by_external_id(self, external_id: str) -> Optional[User]:
        """Find a user by their external ID.

        Args:
            external_id: The user's external identifier.

        Returns:
            The User entity if found, None otherwise.
        """
        user_id = self._external_id_index.get(external_id)
        if user_id:
            return self._users.get(user_id)
        return None

    async def save(self, user: User) -> User:
        """Save a user entity.

        Args:
            user: The User entity to save.

        Returns:
            The saved User entity.
        """
        self._users[user.id] = user
        self._external_id_index[user.external_id] = user.id
        return user
