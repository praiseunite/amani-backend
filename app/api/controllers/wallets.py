"""Wallets controller."""

from uuid import UUID
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.application.use_cases.register_wallet import RegisterWalletUseCase
from app.domain.entities import WalletProvider
from app.api.deps.hmac_auth import HMACAuth


class RegisterWalletRequest(BaseModel):
    """Request model for wallet registration."""

    user_id: UUID = Field(..., description="User ID")
    provider: WalletProvider = Field(..., description="Wallet provider")
    provider_account_id: str = Field(..., description="Provider account ID")
    provider_customer_id: Optional[str] = Field(None, description="Provider customer ID")


class RegisterWalletResponse(BaseModel):
    """Response model for wallet registration."""

    wallet_id: str = Field(..., description="Wallet registry entry ID")
    user_id: str = Field(..., description="User ID")
    provider: str = Field(..., description="Wallet provider")
    is_active: bool = Field(..., description="Whether wallet is active")


def create_wallets_router(
    register_wallet_use_case: RegisterWalletUseCase, hmac_auth: HMACAuth
) -> APIRouter:
    """Create wallets router.

    Args:
        register_wallet_use_case: Use case for registering wallets
        hmac_auth: HMAC authentication dependency

    Returns:
        Configured router
    """
    router = APIRouter(prefix="/wallets", tags=["Wallets"])

    @router.post("/register", response_model=RegisterWalletResponse)
    async def register_wallet(
        request: RegisterWalletRequest, api_key_id: str = Depends(hmac_auth)
    ) -> Dict[str, Any]:
        """Register a wallet (idempotent).

        Requires HMAC authentication.

        Args:
            request: Wallet registration request
            api_key_id: Verified API key ID from HMAC auth

        Returns:
            Registered wallet details
        """
        wallet_entry = await register_wallet_use_case.execute(
            user_id=request.user_id,
            provider=request.provider,
            provider_account_id=request.provider_account_id,
            provider_customer_id=request.provider_customer_id,
        )

        return {
            "wallet_id": str(wallet_entry.id),
            "user_id": str(wallet_entry.user_id),
            "provider": wallet_entry.provider.value,
            "is_active": wallet_entry.is_active,
        }

    return router
