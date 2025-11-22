"""
Wallet routes for wallet registry and balance operations.

Note: Currently only FinCra provider is implemented for balance sync.
Additional providers (Paystack, Flutterwave) can be added by implementing
their respective balance fetch logic.
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.core.fincra import FinCraError, get_fincra_client
from app.crud.wallet import (
    create_wallet_registry,
    get_wallet_registries_by_user,
    get_wallet_registry_by_external_id,
    get_wallet_registry_by_user_and_provider,
)
from app.crud.wallet_balance import (
    create_wallet_balance_snapshot,
    get_latest_wallet_balance_snapshot,
    get_wallet_balance_snapshots_by_wallet,
)
from app.models.user import User
from app.models.wallet_balance_snapshot import WalletBalanceSnapshot
from app.models.wallet_registry import WalletRegistry
from app.schemas.wallet import (
    WalletBalanceSnapshotListResponse,
    WalletBalanceSnapshotResponse,
    WalletRegistryCreate,
    WalletRegistryListResponse,
    WalletRegistryResponse,
    WalletSyncRequest,
)

router = APIRouter(prefix="/wallet", tags=["wallet"])
logger = logging.getLogger(__name__)


@router.post(
    "/register", response_model=WalletRegistryResponse, status_code=status.HTTP_201_CREATED
)
async def register_wallet(
    wallet_data: WalletRegistryCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new wallet for a user.

    Args:
        wallet_data: Wallet registration data
        current_user: Currently authenticated user
        db: Database session

    Returns:
        Created wallet registry entry

    Raises:
        HTTPException: If wallet already exists or registration fails
    """
    # Verify user is registering their own wallet or is admin
    if wallet_data.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only register wallets for yourself",
        )

    # Check if wallet already exists
    existing_wallet = await get_wallet_registry_by_user_and_provider(
        db, wallet_data.user_id, wallet_data.provider
    )

    if existing_wallet:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Wallet for provider {wallet_data.provider} already exists",
        )

    # Create wallet registry entry
    wallet = await create_wallet_registry(
        db=db,
        user_id=wallet_data.user_id,
        provider=wallet_data.provider,
        provider_account_id=wallet_data.provider_account_id,
        provider_customer_id=wallet_data.provider_customer_id,
        metadata=wallet_data.metadata,
    )

    logger.info(f"Wallet registered: {wallet.external_id} for user {wallet_data.user_id}")

    return WalletRegistryResponse.model_validate(wallet)


@router.get("/list", response_model=WalletRegistryListResponse)
async def list_wallets(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List wallets for the current user.

    Args:
        page: Page number
        page_size: Items per page
        current_user: Currently authenticated user
        db: Database session

    Returns:
        Paginated list of wallet registry entries
    """
    # Get user's wallets
    wallets = await get_wallet_registries_by_user(db, current_user.id, active_only=True)

    # Apply pagination
    total = len(wallets)
    start = (page - 1) * page_size
    end = start + page_size
    paginated_wallets = wallets[start:end]
    has_more = end < total

    return WalletRegistryListResponse(
        items=[WalletRegistryResponse.model_validate(w) for w in paginated_wallets],
        total=total,
        page=page,
        page_size=page_size,
        has_more=has_more,
    )


@router.get("/{wallet_id}", response_model=WalletRegistryResponse)
async def get_wallet(
    wallet_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific wallet by ID.

    Args:
        wallet_id: Wallet external UUID
        current_user: Currently authenticated user
        db: Database session

    Returns:
        Wallet registry entry

    Raises:
        HTTPException: If wallet not found or user not authorized
    """
    wallet = await get_wallet_registry_by_external_id(db, wallet_id)

    if not wallet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wallet not found")

    # Check if user has access
    if wallet.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="You don't have access to this wallet"
        )

    return WalletRegistryResponse.model_validate(wallet)


@router.post("/{wallet_id}/sync-balance", response_model=WalletBalanceSnapshotResponse)
async def sync_wallet_balance(
    wallet_id: UUID,
    sync_data: WalletSyncRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Synchronize wallet balance from provider.

    Args:
        wallet_id: Wallet external UUID
        sync_data: Sync request data
        current_user: Currently authenticated user
        db: Database session

    Returns:
        Created balance snapshot

    Raises:
        HTTPException: If wallet not found, user not authorized, or sync fails
    """
    # Get wallet
    wallet = await get_wallet_registry_by_external_id(db, wallet_id)

    if not wallet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wallet not found")

    # Check if user has access
    if wallet.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="You don't have access to this wallet"
        )

    # Fetch balance from provider
    try:
        # Only FinCra is currently implemented
        if wallet.provider != "fincra":
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail=f"Balance sync not yet implemented for provider: {wallet.provider}",
            )

        fincra_client = get_fincra_client()

        # Get balance from FinCra
        balance_response = await fincra_client.get_balance()

        # Extract balance data
        balance_data = balance_response.get("data", {})
        balance_amount = balance_data.get("available_balance", 0)
        currency = balance_data.get("currency", "USD")

        # Create balance snapshot
        snapshot = await create_wallet_balance_snapshot(
            db=db,
            wallet_id=wallet.external_id,
            provider=wallet.provider,
            balance=balance_amount,
            currency=currency,
            external_balance_id=balance_data.get("id"),
            metadata=balance_data,
            idempotency_key=sync_data.idempotency_key,
        )

        logger.info(f"Balance synchronized for wallet {wallet_id}: {balance_amount} {currency}")

        return WalletBalanceSnapshotResponse.model_validate(snapshot)

    except FinCraError as e:
        logger.error(f"FinCra balance sync failed for wallet {wallet_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Balance sync failed: {e.message}",
        )


@router.get("/{wallet_id}/balance", response_model=WalletBalanceSnapshotResponse)
async def get_wallet_balance(
    wallet_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get the latest wallet balance snapshot.

    Args:
        wallet_id: Wallet external UUID
        current_user: Currently authenticated user
        db: Database session

    Returns:
        Latest balance snapshot

    Raises:
        HTTPException: If wallet not found, user not authorized, or no balance snapshot found
    """
    # Get wallet
    wallet = await get_wallet_registry_by_external_id(db, wallet_id)

    if not wallet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wallet not found")

    # Check if user has access
    if wallet.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="You don't have access to this wallet"
        )

    # Get latest balance snapshot
    snapshot = await get_latest_wallet_balance_snapshot(db, wallet.external_id)

    if not snapshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No balance snapshot found"
        )

    return WalletBalanceSnapshotResponse.model_validate(snapshot)


@router.get("/{wallet_id}/balance/history", response_model=WalletBalanceSnapshotListResponse)
async def get_wallet_balance_history(
    wallet_id: UUID,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get wallet balance history.

    Args:
        wallet_id: Wallet external UUID
        page: Page number
        page_size: Items per page
        current_user: Currently authenticated user
        db: Database session

    Returns:
        Paginated list of balance snapshots

    Raises:
        HTTPException: If wallet not found or user not authorized
    """
    # Get wallet
    wallet = await get_wallet_registry_by_external_id(db, wallet_id)

    if not wallet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wallet not found")

    # Check if user has access
    if wallet.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="You don't have access to this wallet"
        )

    # Get balance snapshots
    offset = (page - 1) * page_size
    snapshots = await get_wallet_balance_snapshots_by_wallet(
        db, wallet.external_id, limit=page_size + 1, offset=offset
    )

    # Check if there are more items
    has_more = len(snapshots) > page_size
    items = snapshots[:page_size]

    # Get total count (simplified - would need a count query for accurate pagination)
    total = offset + len(snapshots)

    return WalletBalanceSnapshotListResponse(
        items=[WalletBalanceSnapshotResponse.model_validate(s) for s in items],
        total=total,
        page=page,
        page_size=page_size,
        has_more=has_more,
    )
