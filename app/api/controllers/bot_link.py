"""Bot link controller."""

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from app.application.use_cases.consume_link_token import ConsumeLinkTokenUseCase
from app.api.deps.hmac_auth import HMACAuth


class BotLinkRequest(BaseModel):
    """Request model for bot linking."""

    token: str = Field(..., description="Link token")
    provider_account_id: str = Field(..., description="Provider account ID")
    provider_customer_id: Optional[str] = Field(None, description="Provider customer ID")


class BotLinkResponse(BaseModel):
    """Response model for bot linking."""

    success: bool = Field(..., description="Whether linking was successful")
    wallet_id: str = Field(..., description="Wallet registry entry ID")
    user_id: str = Field(..., description="User ID")


def create_bot_link_router(
    consume_link_token_use_case: ConsumeLinkTokenUseCase, hmac_auth: HMACAuth
) -> APIRouter:
    """Create bot link router.

    Args:
        consume_link_token_use_case: Use case for consuming link tokens
        hmac_auth: HMAC authentication dependency

    Returns:
        Configured router
    """
    router = APIRouter(prefix="/bot", tags=["Bot"])

    @router.post("/link", response_model=BotLinkResponse)
    async def link_bot(
        request: BotLinkRequest, api_key_id: str = Depends(hmac_auth)
    ) -> Dict[str, Any]:
        """Link a bot/provider account using a link token.

        Requires HMAC authentication.

        Args:
            request: Bot link request
            api_key_id: Verified API key ID from HMAC auth

        Returns:
            Bot linking result

        Raises:
            HTTPException: If token is invalid or already consumed
        """
        wallet_entry = await consume_link_token_use_case.execute(
            token=request.token,
            provider_account_id=request.provider_account_id,
            provider_customer_id=request.provider_customer_id,
        )

        if wallet_entry is None:
            raise HTTPException(
                status_code=400, detail="Invalid, expired, or already consumed link token"
            )

        return {
            "success": True,
            "wallet_id": str(wallet_entry.id),
            "user_id": str(wallet_entry.user_id),
        }

    return router
