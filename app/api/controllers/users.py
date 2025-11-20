"""Users controller."""

from uuid import UUID
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Optional

from app.application.use_cases.get_user_status import GetUserStatusUseCase


class UserStatusResponse(BaseModel):
    """Response model for user status."""

    user_id: str
    email: str
    full_name: Optional[str]
    role: str
    is_active: bool
    is_verified: bool


def create_users_router(get_user_status_use_case: GetUserStatusUseCase):
    """Create users router.

    Args:
        get_user_status_use_case: Use case for getting user status

    Returns:
        FastAPI router
    """
    router = APIRouter(prefix="/users", tags=["users"])

    @router.get("/{user_id}/status", response_model=UserStatusResponse)
    async def get_user_status(user_id: UUID):
        """Get user status.

        Args:
            user_id: User's unique identifier

        Returns:
            User status information
        """
        user = await get_user_status_use_case.execute(user_id)

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        return UserStatusResponse(
            user_id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            is_verified=user.is_verified,
        )

    return router
