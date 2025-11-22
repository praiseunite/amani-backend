"""
CRUD operations for wallet balance snapshots.
"""

from typing import Optional, List
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.wallet_balance_snapshot import WalletBalanceSnapshot


async def create_wallet_balance_snapshot(
    db: AsyncSession,
    wallet_id: UUID,
    provider: str,
    balance: Decimal,
    currency: str = "USD",
    external_balance_id: Optional[str] = None,
    as_of: Optional[datetime] = None,
    metadata: Optional[dict] = None,
    idempotency_key: Optional[str] = None,
) -> WalletBalanceSnapshot:
    """
    Create a new wallet balance snapshot.

    Args:
        db: Database session
        wallet_id: Wallet UUID
        provider: Wallet provider name
        balance: Balance amount
        currency: Currency code (default USD)
        external_balance_id: Optional external balance ID from provider
        as_of: Timestamp of the balance (default current time)
        metadata: Optional metadata dictionary
        idempotency_key: Optional idempotency key

    Returns:
        Created wallet balance snapshot
    """
    snapshot = WalletBalanceSnapshot(
        wallet_id=wallet_id,
        provider=provider,
        balance=balance,
        currency=currency,
        external_balance_id=external_balance_id,
        as_of=as_of or datetime.utcnow(),
        extra_data=metadata or {},
        idempotency_key=idempotency_key,
    )

    db.add(snapshot)
    await db.commit()
    await db.refresh(snapshot)

    return snapshot


async def get_wallet_balance_snapshot_by_id(
    db: AsyncSession, snapshot_id: UUID
) -> Optional[WalletBalanceSnapshot]:
    """
    Get wallet balance snapshot by ID.

    Args:
        db: Database session
        snapshot_id: Snapshot UUID

    Returns:
        Wallet balance snapshot or None
    """
    result = await db.execute(
        select(WalletBalanceSnapshot).where(WalletBalanceSnapshot.id == snapshot_id)
    )
    return result.scalar_one_or_none()


async def get_wallet_balance_snapshot_by_idempotency_key(
    db: AsyncSession, idempotency_key: str
) -> Optional[WalletBalanceSnapshot]:
    """
    Get wallet balance snapshot by idempotency key.

    Args:
        db: Database session
        idempotency_key: Idempotency key

    Returns:
        Wallet balance snapshot or None
    """
    result = await db.execute(
        select(WalletBalanceSnapshot).where(
            WalletBalanceSnapshot.idempotency_key == idempotency_key
        )
    )
    return result.scalar_one_or_none()


async def get_latest_wallet_balance_snapshot(
    db: AsyncSession, wallet_id: UUID
) -> Optional[WalletBalanceSnapshot]:
    """
    Get the most recent wallet balance snapshot for a wallet.

    Args:
        db: Database session
        wallet_id: Wallet UUID

    Returns:
        Latest wallet balance snapshot or None
    """
    result = await db.execute(
        select(WalletBalanceSnapshot)
        .where(WalletBalanceSnapshot.wallet_id == wallet_id)
        .order_by(desc(WalletBalanceSnapshot.as_of))
        .limit(1)
    )
    return result.scalar_one_or_none()


async def get_wallet_balance_snapshots_by_wallet(
    db: AsyncSession, wallet_id: UUID, limit: int = 100, offset: int = 0
) -> List[WalletBalanceSnapshot]:
    """
    Get wallet balance snapshots for a wallet with pagination.

    Args:
        db: Database session
        wallet_id: Wallet UUID
        limit: Maximum number of snapshots to return
        offset: Number of snapshots to skip

    Returns:
        List of wallet balance snapshots
    """
    result = await db.execute(
        select(WalletBalanceSnapshot)
        .where(WalletBalanceSnapshot.wallet_id == wallet_id)
        .order_by(desc(WalletBalanceSnapshot.as_of))
        .limit(limit)
        .offset(offset)
    )
    return list(result.scalars().all())


async def get_wallet_balance_snapshot_by_external_id(
    db: AsyncSession, external_balance_id: str
) -> Optional[WalletBalanceSnapshot]:
    """
    Get wallet balance snapshot by external balance ID.

    Args:
        db: Database session
        external_balance_id: External balance ID from provider

    Returns:
        Wallet balance snapshot or None
    """
    result = await db.execute(
        select(WalletBalanceSnapshot).where(
            WalletBalanceSnapshot.external_balance_id == external_balance_id
        )
    )
    return result.scalar_one_or_none()


async def delete_wallet_balance_snapshot(db: AsyncSession, snapshot_id: UUID) -> bool:
    """
    Delete a wallet balance snapshot (hard delete).

    Args:
        db: Database session
        snapshot_id: Snapshot UUID

    Returns:
        True if deleted, False if not found
    """
    snapshot = await get_wallet_balance_snapshot_by_id(db, snapshot_id)
    if not snapshot:
        return False

    await db.delete(snapshot)
    await db.commit()

    return True
