"""Link tokens controller."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel

from app.application.use_cases.create_link_token import CreateLinkTokenUseCase
from app.domain.entities import WalletProvider


class CreateLinkTokenRequest(BaseModel):
    """Request model for creating a link token."""

    provider: WalletProvider


class CreateLinkTokenResponse(BaseModel):
    """Response model for creating a link token."""

    token: str
    expires_at: str
    provider: str


def create_link_tokens_router(create_link_token_use_case: CreateLinkTokenUseCase):
    """Create link tokens router.

    Args:
        create_link_token_use_case: Use case for creating link tokens

    Returns:
        FastAPI router
    """
    router = APIRouter(prefix="/link_tokens", tags=["link_tokens"])

    @router.post("/create", response_model=CreateLinkTokenResponse)
    async def create_link_token(
        request: CreateLinkTokenRequest,
        x_user_id: Optional[str] = Header(None, alias="X-USER-ID"),
    ):
        """Create a link token for connecting a wallet.

        Requires X-USER-ID header for simulated authentication.

        Args:
            request: Create link token request
            x_user_id: User ID from header

        Returns:
            Created link token information
        """
        if not x_user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing X-USER-ID header",
            )

        try:
            user_id = UUID(x_user_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user ID format",
            )

        link_token = await create_link_token_use_case.execute(
            user_id=user_id,
            provider=request.provider,
        )

        return CreateLinkTokenResponse(
            token=link_token.token,
            expires_at=link_token.expires_at.isoformat(),
            provider=link_token.provider.value,
        )

    return router
