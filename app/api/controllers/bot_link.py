"""Bot link controller."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.application.use_cases.bot_link import BotLinkUseCase


class BotLinkRequest(BaseModel):
    """Request model for bot linking."""

    token: str
    provider_account_id: str


class BotLinkResponse(BaseModel):
    """Response model for bot linking."""

    success: bool
    message: str


def create_bot_link_router(
    bot_link_use_case: BotLinkUseCase,
    hmac_auth_dependency,
):
    """Create bot link router.

    Args:
        bot_link_use_case: Use case for bot linking
        hmac_auth_dependency: HMAC auth dependency

    Returns:
        FastAPI router
    """
    router = APIRouter(prefix="/bot", tags=["bot"])

    @router.post("/link", response_model=BotLinkResponse)
    async def link_bot(
        request: BotLinkRequest,
        api_key_id: str = Depends(hmac_auth_dependency),
    ):
        """Link a bot wallet using a link token.

        Requires HMAC authentication.

        Args:
            request: Bot link request
            api_key_id: Authenticated API key ID

        Returns:
            Bot link response
        """
        consumed_token = await bot_link_use_case.execute(
            token=request.token,
            provider_account_id=request.provider_account_id,
        )

        if consumed_token is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired token",
            )

        return BotLinkResponse(
            success=True,
            message="Bot linked successfully",
        )

    return router
