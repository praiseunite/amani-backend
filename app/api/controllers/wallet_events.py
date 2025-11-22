"""Wallet events controller."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.application.use_cases.wallet_events import (
    IngestWalletEventUseCase,
    ListWalletEventsUseCase,
)
from app.domain.entities import WalletEventType, WalletProvider


class IngestEventRequest(BaseModel):
    """Request model for event ingestion."""

    wallet_id: UUID
    provider: WalletProvider
    event_type: WalletEventType
    amount: float
    currency: str
    occurred_at: datetime
    provider_event_id: Optional[str] = None
    metadata: Optional[dict] = None
    idempotency_key: Optional[str] = None


class WalletEventResponse(BaseModel):
    """Response model for wallet event."""

    event_id: str
    wallet_id: str
    provider: str
    event_type: str
    amount: float
    currency: str
    provider_event_id: Optional[str]
    metadata: dict
    occurred_at: datetime
    created_at: datetime


class EventListResponse(BaseModel):
    """Response model for event list."""

    events: List[WalletEventResponse]
    total: int
    limit: int
    offset: int


def create_wallet_events_router(
    ingest_event_use_case: IngestWalletEventUseCase,
    list_events_use_case: ListWalletEventsUseCase,
    hmac_auth_dependency,
):
    """Create wallet events router.

    Args:
        ingest_event_use_case: Use case for event ingestion
        list_events_use_case: Use case for listing events
        hmac_auth_dependency: HMAC auth dependency

    Returns:
        FastAPI router
    """
    router = APIRouter(prefix="/wallets", tags=["wallet-events"])

    @router.post("/{wallet_id}/events/ingest", response_model=WalletEventResponse)
    async def ingest_event(
        wallet_id: UUID,
        request: IngestEventRequest,
        api_key_id: str = Depends(hmac_auth_dependency),
    ):
        """Ingest a wallet transaction event (idempotent).

        Requires HMAC authentication.

        Args:
            wallet_id: The wallet's unique identifier
            request: Event ingestion request
            api_key_id: Authenticated API key ID

        Returns:
            Ingested event information
        """
        # Validate wallet_id matches request
        if wallet_id != request.wallet_id:
            raise HTTPException(
                status_code=400,
                detail="wallet_id in path must match wallet_id in request body",
            )

        event = await ingest_event_use_case.execute(
            wallet_id=request.wallet_id,
            provider=request.provider,
            event_type=request.event_type,
            amount=request.amount,
            currency=request.currency,
            occurred_at=request.occurred_at,
            provider_event_id=request.provider_event_id,
            metadata=request.metadata,
            idempotency_key=request.idempotency_key,
        )

        return WalletEventResponse(
            event_id=str(event.id),
            wallet_id=str(event.wallet_id),
            provider=event.provider.value,
            event_type=event.event_type.value,
            amount=event.amount,
            currency=event.currency,
            provider_event_id=event.provider_event_id,
            metadata=event.metadata,
            occurred_at=event.occurred_at,
            created_at=event.created_at,
        )

    @router.get("/{wallet_id}/events", response_model=EventListResponse)
    async def list_events(
        wallet_id: UUID,
        limit: int = 100,
        offset: int = 0,
        api_key_id: str = Depends(hmac_auth_dependency),
    ):
        """List wallet transaction events.

        Requires HMAC authentication.

        Args:
            wallet_id: The wallet's unique identifier
            limit: Maximum number of events to return (default 100, max 1000)
            offset: Number of events to skip (default 0)
            api_key_id: Authenticated API key ID

        Returns:
            List of wallet transaction events
        """
        # Validate pagination parameters
        if limit < 1 or limit > 1000:
            raise HTTPException(status_code=400, detail="limit must be between 1 and 1000")
        if offset < 0:
            raise HTTPException(status_code=400, detail="offset must be non-negative")

        events = await list_events_use_case.execute(
            wallet_id=wallet_id,
            limit=limit,
            offset=offset,
        )

        return EventListResponse(
            events=[
                WalletEventResponse(
                    event_id=str(event.id),
                    wallet_id=str(event.wallet_id),
                    provider=event.provider.value,
                    event_type=event.event_type.value,
                    amount=event.amount,
                    currency=event.currency,
                    provider_event_id=event.provider_event_id,
                    metadata=event.metadata,
                    occurred_at=event.occurred_at,
                    created_at=event.created_at,
                )
                for event in events
            ],
            total=len(events),
            limit=limit,
            offset=offset,
        )

    return router
