"""
CRUD operations for wallet transaction events.
"""

from typing import Optional, List
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.wallet_event import WalletTransactionEvent


async def create_wallet_event(
    db: AsyncSession,
    wallet_id: UUID,
    provider: str,
    event_type: str,
    amount: float,
    currency: str = "USD",
    provider_event_id: Optional[str] = None,
    occurred_at: Optional[datetime] = None,
    metadata: Optional[dict] = None,
    idempotency_key: Optional[str] = None,
) -> WalletTransactionEvent:
    """
    Create a new wallet transaction event.

    Args:
        db: Database session
        wallet_id: Wallet UUID
        provider: Wallet provider name
        event_type: Event type
        amount: Transaction amount
        currency: Currency code (default USD)
        provider_event_id: Optional provider event ID
        occurred_at: Timestamp when event occurred (default current time)
        metadata: Optional metadata dictionary
        idempotency_key: Optional idempotency key

    Returns:
        Created wallet transaction event
    """
    event = WalletTransactionEvent(
        wallet_id=wallet_id,
        provider=provider,
        event_type=event_type,
        amount=amount,
        currency=currency,
        provider_event_id=provider_event_id,
        occurred_at=occurred_at or datetime.utcnow(),
        extra_data=metadata or {},
        idempotency_key=idempotency_key,
    )

    db.add(event)
    await db.commit()
    await db.refresh(event)

    return event


async def get_wallet_event_by_id(db: AsyncSession, event_id: int) -> Optional[WalletTransactionEvent]:
    """
    Get wallet transaction event by internal ID.

    Args:
        db: Database session
        event_id: Internal event ID

    Returns:
        Wallet transaction event or None
    """
    result = await db.execute(
        select(WalletTransactionEvent).where(WalletTransactionEvent.id == event_id)
    )
    return result.scalar_one_or_none()


async def get_wallet_event_by_external_id(
    db: AsyncSession, external_id: UUID
) -> Optional[WalletTransactionEvent]:
    """
    Get wallet transaction event by external UUID.

    Args:
        db: Database session
        external_id: External UUID

    Returns:
        Wallet transaction event or None
    """
    result = await db.execute(
        select(WalletTransactionEvent).where(WalletTransactionEvent.external_id == external_id)
    )
    return result.scalar_one_or_none()


async def get_wallet_event_by_idempotency_key(
    db: AsyncSession, idempotency_key: str
) -> Optional[WalletTransactionEvent]:
    """
    Get wallet transaction event by idempotency key.

    Args:
        db: Database session
        idempotency_key: Idempotency key

    Returns:
        Wallet transaction event or None
    """
    result = await db.execute(
        select(WalletTransactionEvent).where(
            WalletTransactionEvent.idempotency_key == idempotency_key
        )
    )
    return result.scalar_one_or_none()


async def get_wallet_events_by_wallet(
    db: AsyncSession, wallet_id: UUID, limit: int = 100, offset: int = 0
) -> List[WalletTransactionEvent]:
    """
    Get wallet transaction events for a wallet with pagination.

    Args:
        db: Database session
        wallet_id: Wallet UUID
        limit: Maximum number of events to return
        offset: Number of events to skip

    Returns:
        List of wallet transaction events
    """
    result = await db.execute(
        select(WalletTransactionEvent)
        .where(WalletTransactionEvent.wallet_id == wallet_id)
        .order_by(desc(WalletTransactionEvent.occurred_at))
        .limit(limit)
        .offset(offset)
    )
    return list(result.scalars().all())


async def get_wallet_events_by_provider_event_id(
    db: AsyncSession, provider_event_id: str
) -> Optional[WalletTransactionEvent]:
    """
    Get wallet transaction event by provider event ID.

    Args:
        db: Database session
        provider_event_id: Provider event ID

    Returns:
        Wallet transaction event or None
    """
    result = await db.execute(
        select(WalletTransactionEvent).where(
            WalletTransactionEvent.provider_event_id == provider_event_id
        )
    )
    return result.scalar_one_or_none()


async def get_wallet_events_by_type(
    db: AsyncSession, wallet_id: UUID, event_type: str, limit: int = 100, offset: int = 0
) -> List[WalletTransactionEvent]:
    """
    Get wallet transaction events by wallet and event type.

    Args:
        db: Database session
        wallet_id: Wallet UUID
        event_type: Event type
        limit: Maximum number of events to return
        offset: Number of events to skip

    Returns:
        List of wallet transaction events
    """
    result = await db.execute(
        select(WalletTransactionEvent)
        .where(
            and_(
                WalletTransactionEvent.wallet_id == wallet_id,
                WalletTransactionEvent.event_type == event_type,
            )
        )
        .order_by(desc(WalletTransactionEvent.occurred_at))
        .limit(limit)
        .offset(offset)
    )
    return list(result.scalars().all())


async def delete_wallet_event(db: AsyncSession, event_id: int) -> bool:
    """
    Delete a wallet transaction event (hard delete).

    Args:
        db: Database session
        event_id: Internal event ID

    Returns:
        True if deleted, False if not found
    """
    event = await get_wallet_event_by_id(db, event_id)
    if not event:
        return False

    await db.delete(event)
    await db.commit()

    return True
