"""Users controller."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel

from app.application.use_cases.get_user_status import GetUserStatusUseCase


class UserStatusResponse(BaseModel):
    """Response model for user status."""

    user_id: str
    email: str
    full_name: Optional[str]
    role: str
    is_active: bool
    is_verified: bool


def create_users_router(
    get_user_status_use_case: GetUserStatusUseCase,
    hmac_auth_dependency,
):
    """Create users router.

    Args:
        get_user_status_use_case: Use case for getting user status
        hmac_auth_dependency: HMAC auth dependency

    Returns:
        FastAPI router
    """
    router = APIRouter(prefix="/users", tags=["users"])

    @router.get("/{user_id}/status", response_model=UserStatusResponse)
    async def get_user_status(
        user_id: UUID,
        x_user_id: Optional[str] = Header(None, alias="X-USER-ID"),
        x_api_key_id: Optional[str] = Header(None, alias="X-API-KEY-ID"),
        x_api_timestamp: Optional[str] = Header(None, alias="X-API-TIMESTAMP"),
        x_api_signature: Optional[str] = Header(None, alias="X-API-SIGNATURE"),
        # We cannot use Depends(hmac_auth_dependency) directly here because it's optional
        # depending on whether X-USER-ID is present.
        # We need to check conditions manually or use a custom dependency.
    ):
        """Get user status.

        Protected by HMAC auth or optional user header for tests/frontend.

        Args:
            user_id: User's unique identifier
            x_user_id: Optional user ID header for simulated auth
            x_api_key_id: Optional HMAC key ID
            x_api_timestamp: Optional HMAC timestamp
            x_api_signature: Optional HMAC signature

        Returns:
            User status information
        """
        # Check if authenticated via X-USER-ID (simulated/frontend) or HMAC (service)
        is_hmac = x_api_key_id and x_api_timestamp and x_api_signature
        is_user_auth = x_user_id is not None

        if not is_hmac and not is_user_auth:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing authentication headers",
            )

        if is_hmac:
            # Manually invoke HMAC verification if headers are present
            # Note: We need to pass the values to the dependency logic.
            # Since hmac_auth_dependency is a function that takes specific args (as Depends),
            # we can call it directly if it was just a function, but since it's designed for Depends,
            # we might need to call the underlying logic or reuse the dependency.
            # For simplicity here, we will call the verification method of the class if we had access,
            # but here we have the dependency function itself.
            # The dependency function `hmac_auth.verify` expects params injected by FastAPI.
            # We can call it directly.
            await hmac_auth_dependency(
                x_api_key_id=x_api_key_id,
                x_api_timestamp=x_api_timestamp,
                x_api_signature=x_api_signature,
            )

        if is_user_auth:
            # If using user auth, verify the requesting user matches the target user
            # or has admin permissions (omitted for simplicity).
            if x_user_id != str(user_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to view this user status",
                )

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
