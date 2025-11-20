"""Users controller."""

from uuid import UUID
from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.application.use_cases.get_user_status import GetUserStatusUseCase


class UserStatusResponse(BaseModel):
    """Response model for user status."""

    id: str = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    role: str = Field(..., description="User role")
    is_active: bool = Field(..., description="Whether user is active")
    is_verified: bool = Field(..., description="Whether user is verified")


def create_users_router(get_user_status_use_case: GetUserStatusUseCase) -> APIRouter:
    """Create users router.

    Args:
        get_user_status_use_case: Use case for getting user status

    Returns:
        Configured router
    """
    router = APIRouter(prefix="/users", tags=["Users"])

    @router.get("/{user_id}/status", response_model=UserStatusResponse)
    async def get_user_status(user_id: UUID) -> Dict[str, Any]:
        """Get user status by ID.

        Args:
            user_id: User ID

        Returns:
            User status details

        Raises:
            HTTPException: If user not found
        """
        user = await get_user_status_use_case.execute(user_id)

        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        return {
            "id": str(user.id),
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
        }

    return router
