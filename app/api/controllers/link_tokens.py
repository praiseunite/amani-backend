"""Link tokens controller."""

from uuid import UUID
from fastapi import APIRouter
from pydantic import BaseModel

from app.domain.entities import WalletProvider
from app.application.use_cases.create_link_token import CreateLinkTokenUseCase


class CreateLinkTokenRequest(BaseModel):
    """Request model for creating a link token."""

    user_id: UUID
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
    async def create_link_token(request: CreateLinkTokenRequest):
        """Create a link token for connecting a wallet.

        Args:
            request: Create link token request

        Returns:
            Created link token information
        """
        link_token = await create_link_token_use_case.execute(
            user_id=request.user_id,
            provider=request.provider,
        )

        return CreateLinkTokenResponse(
            token=link_token.token,
            expires_at=link_token.expires_at.isoformat(),
            provider=link_token.provider.value,
        )

    return router
