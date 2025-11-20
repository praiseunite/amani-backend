"""Get user status use case."""

from typing import Optional
from uuid import UUID

from app.domain.entities import User
from app.ports.user_repository import UserRepositoryPort


class GetUserStatusUseCase:
    """Use case for getting user status."""

    def __init__(self, user_repository_port: UserRepositoryPort):
        """Initialize use case.

        Args:
            user_repository_port: The user repository port
        """
        self.user_repository_port = user_repository_port

    async def execute(self, user_id: UUID) -> Optional[User]:
        """Execute the use case.

        Args:
            user_id: The user's unique identifier

        Returns:
            The user if found, None otherwise
        """
        return await self.user_repository_port.find_by_id(user_id)
