"""Link token controller."""

from uuid import UUID
from typing import Any, Dict

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.application.use_cases.create_link_token import CreateLinkTokenUseCase
from app.domain.entities import WalletProvider


class CreateLinkTokenRequest(BaseModel):
    """Request model for creating a link token."""

    user_id: UUID = Field(..., description="User ID")
    provider: WalletProvider = Field(..., description="Wallet provider")


class CreateLinkTokenResponse(BaseModel):
    """Response model for link token creation."""

    token: str = Field(..., description="Link token")
    expires_at: str = Field(..., description="Token expiry timestamp (ISO format)")
    provider: str = Field(..., description="Wallet provider")


def create_link_tokens_router(create_link_token_use_case: CreateLinkTokenUseCase) -> APIRouter:
    """Create link tokens router.

    Args:
        create_link_token_use_case: Use case for creating link tokens

    Returns:
        Configured router
    """
    router = APIRouter(prefix="/link_tokens", tags=["Link Tokens"])

    @router.post("/create", response_model=CreateLinkTokenResponse, status_code=201)
    async def create_link_token(request: CreateLinkTokenRequest) -> Dict[str, Any]:
        """Create a link token for connecting a wallet.

        Args:
            request: Link token creation request

        Returns:
            Created link token details
        """
        link_token = await create_link_token_use_case.execute(
            user_id=request.user_id, provider=request.provider
        )

        return {
            "token": link_token.token,
            "expires_at": link_token.expires_at.isoformat(),
            "provider": link_token.provider.value,
        }

    return router
