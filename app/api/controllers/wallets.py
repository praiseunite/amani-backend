"""Wallets controller."""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.domain.entities import WalletProvider
from app.application.use_cases.register_wallet import RegisterWalletUseCase
from app.application.use_cases.sync_wallet_balance import SyncWalletBalanceUseCase


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


class SyncBalanceRequest(BaseModel):
    """Request model for balance synchronization."""

    wallet_id: UUID
    idempotency_key: Optional[str] = None


class BalanceSnapshotResponse(BaseModel):
    """Response model for balance snapshot."""

    snapshot_id: str
    wallet_id: str
    provider: str
    balance: float
    currency: str
    external_balance_id: Optional[str]
    as_of: datetime
    created_at: datetime


def create_wallets_router(
    register_wallet_use_case: RegisterWalletUseCase,
    hmac_auth_dependency,
    sync_wallet_balance_use_case: Optional[SyncWalletBalanceUseCase] = None,
):
    """Create wallets router.

    Args:
        register_wallet_use_case: Use case for wallet registration
        hmac_auth_dependency: HMAC auth dependency (required)
        sync_wallet_balance_use_case: Use case for wallet balance synchronization

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

    # Only add sync endpoint if use case is provided
    if sync_wallet_balance_use_case:

        @router.post("/{wallet_id}/sync-balance", response_model=BalanceSnapshotResponse)
        async def sync_balance(
            wallet_id: UUID,
            idempotency_key: Optional[str] = None,
            api_key_id: str = Depends(hmac_auth_dependency),
        ):
            """Synchronize wallet balance (idempotent).

            Fetches the current balance from the provider and creates a snapshot.
            Requires HMAC authentication.

            Args:
                wallet_id: The wallet's unique identifier
                idempotency_key: Optional idempotency key for duplicate prevention
                api_key_id: Authenticated API key ID

            Returns:
                Balance snapshot information
            """
            snapshot = await sync_wallet_balance_use_case.execute(
                wallet_id=wallet_id,
                idempotency_key=idempotency_key,
            )

            return BalanceSnapshotResponse(
                snapshot_id=str(snapshot.id),
                wallet_id=str(snapshot.wallet_id),
                provider=snapshot.provider.value,
                balance=snapshot.balance,
                currency=snapshot.currency,
                external_balance_id=snapshot.external_balance_id,
                as_of=snapshot.as_of,
                created_at=snapshot.created_at,
            )

        @router.get("/{wallet_id}/balance", response_model=BalanceSnapshotResponse)
        async def get_balance(
            wallet_id: UUID,
            api_key_id: str = Depends(hmac_auth_dependency),
        ):
            """Get latest balance snapshot for a wallet.

            Requires HMAC authentication.

            Args:
                wallet_id: The wallet's unique identifier
                api_key_id: Authenticated API key ID

            Returns:
                Latest balance snapshot information

            Raises:
                HTTPException: If no balance snapshot found
            """
            snapshot = await sync_wallet_balance_use_case.get_latest(wallet_id=wallet_id)

            if snapshot is None:
                raise HTTPException(status_code=404, detail="No balance snapshot found")

            return BalanceSnapshotResponse(
                snapshot_id=str(snapshot.id),
                wallet_id=str(snapshot.wallet_id),
                provider=snapshot.provider.value,
                balance=snapshot.balance,
                currency=snapshot.currency,
                external_balance_id=snapshot.external_balance_id,
                as_of=snapshot.as_of,
                created_at=snapshot.created_at,
            )

    return router
