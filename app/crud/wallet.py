"""
CRUD operations for wallet registry.
"""

from typing import Optional, List
from uuid import UUID
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.wallet_registry import WalletRegistry


async def create_wallet_registry(
    db: AsyncSession,
    user_id: UUID,
    provider: str,
    provider_account_id: str,
    provider_customer_id: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> WalletRegistry:
    """
    Create a new wallet registry entry.

    Args:
        db: Database session
        user_id: User UUID
        provider: Wallet provider name
        provider_account_id: Provider's account ID
        provider_customer_id: Optional provider customer ID
        metadata: Optional metadata dictionary

    Returns:
        Created wallet registry entry
    """
    wallet = WalletRegistry(
        user_id=user_id,
        provider=provider,
        provider_account_id=provider_account_id,
        provider_customer_id=provider_customer_id,
        extra_data=metadata or {},
    )

    db.add(wallet)
    await db.commit()
    await db.refresh(wallet)

    return wallet


async def get_wallet_registry_by_id(db: AsyncSession, wallet_id: int) -> Optional[WalletRegistry]:
    """
    Get wallet registry entry by internal ID.

    Args:
        db: Database session
        wallet_id: Internal wallet ID

    Returns:
        Wallet registry entry or None
    """
    result = await db.execute(select(WalletRegistry).where(WalletRegistry.id == wallet_id))
    return result.scalar_one_or_none()


async def get_wallet_registry_by_external_id(
    db: AsyncSession, external_id: UUID
) -> Optional[WalletRegistry]:
    """
    Get wallet registry entry by external UUID.

    Args:
        db: Database session
        external_id: External UUID

    Returns:
        Wallet registry entry or None
    """
    result = await db.execute(
        select(WalletRegistry).where(WalletRegistry.external_id == external_id)
    )
    return result.scalar_one_or_none()


async def get_wallet_registry_by_user_and_provider(
    db: AsyncSession, user_id: UUID, provider: str
) -> Optional[WalletRegistry]:
    """
    Get wallet registry entry by user ID and provider.

    Args:
        db: Database session
        user_id: User UUID
        provider: Wallet provider name

    Returns:
        Wallet registry entry or None
    """
    result = await db.execute(
        select(WalletRegistry).where(
            and_(WalletRegistry.user_id == user_id, WalletRegistry.provider == provider)
        )
    )
    return result.scalar_one_or_none()


async def get_wallet_registries_by_user(
    db: AsyncSession, user_id: UUID, active_only: bool = True
) -> List[WalletRegistry]:
    """
    Get all wallet registry entries for a user.

    Args:
        db: Database session
        user_id: User UUID
        active_only: If True, return only active wallets

    Returns:
        List of wallet registry entries
    """
    query = select(WalletRegistry).where(WalletRegistry.user_id == user_id)

    if active_only:
        query = query.where(WalletRegistry.is_active == True)

    result = await db.execute(query.order_by(WalletRegistry.created_at.desc()))
    return list(result.scalars().all())


async def update_wallet_registry(
    db: AsyncSession, wallet_id: int, **kwargs
) -> Optional[WalletRegistry]:
    """
    Update wallet registry entry.

    Args:
        db: Database session
        wallet_id: Internal wallet ID
        **kwargs: Fields to update

    Returns:
        Updated wallet registry entry or None
    """
    wallet = await get_wallet_registry_by_id(db, wallet_id)
    if not wallet:
        return None

    for key, value in kwargs.items():
        if hasattr(wallet, key):
            setattr(wallet, key, value)

    await db.commit()
    await db.refresh(wallet)

    return wallet


async def deactivate_wallet_registry(db: AsyncSession, wallet_id: int) -> bool:
    """
    Deactivate a wallet registry entry.

    Args:
        db: Database session
        wallet_id: Internal wallet ID

    Returns:
        True if deactivated, False if not found
    """
    wallet = await get_wallet_registry_by_id(db, wallet_id)
    if not wallet:
        return False

    wallet.is_active = False
    await db.commit()

    return True


async def delete_wallet_registry(db: AsyncSession, wallet_id: int) -> bool:
    """
    Delete a wallet registry entry (hard delete).

    Args:
        db: Database session
        wallet_id: Internal wallet ID

    Returns:
        True if deleted, False if not found
    """
    wallet = await get_wallet_registry_by_id(db, wallet_id)
    if not wallet:
        return False

    await db.delete(wallet)
    await db.commit()

    return True
