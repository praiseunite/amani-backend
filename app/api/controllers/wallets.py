"""Wallets controller."""

from uuid import UUID
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional

from app.domain.entities import WalletProvider
from app.application.use_cases.register_wallet import RegisterWalletUseCase


class RegisterWalletRequest(BaseModel):
    """Request model for wallet registration."""

    user_id: UUID
    provider: WalletProvider
    provider_account_id: str
    provider_customer_id: Optional[str] = None
    metadata: Optional[dict] = None


class RegisterWalletResponse(BaseModel):
    """Response model for wallet registration."""

    wallet_id: str
    user_id: str
    provider: str
    provider_account_id: str
    is_active: bool


def create_wallets_router(
    register_wallet_use_case: RegisterWalletUseCase,
    hmac_auth_dependency,
):
    """Create wallets router.

    Args:
        register_wallet_use_case: Use case for wallet registration
        hmac_auth_dependency: HMAC auth dependency

    Returns:
        FastAPI router
    """
    router = APIRouter(prefix="/wallets", tags=["wallets"])

    @router.post("/register", response_model=RegisterWalletResponse)
    async def register_wallet(
        request: RegisterWalletRequest,
        api_key_id: str = Depends(hmac_auth_dependency),
    ):
        """Register a wallet for a user (idempotent).

        Requires HMAC authentication.

        Args:
            request: Wallet registration request
            api_key_id: Authenticated API key ID

        Returns:
            Registered wallet information
        """
        wallet_entry = await register_wallet_use_case.execute(
            user_id=request.user_id,
            provider=request.provider,
            provider_account_id=request.provider_account_id,
            provider_customer_id=request.provider_customer_id,
            metadata=request.metadata,
        )

        return RegisterWalletResponse(
            wallet_id=str(wallet_entry.id),
            user_id=str(wallet_entry.user_id),
            provider=wallet_entry.provider.value,
            provider_account_id=wallet_entry.provider_account_id,
            is_active=wallet_entry.is_active,
        )

    return router
