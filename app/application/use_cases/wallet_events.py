"""Use case for ingesting wallet transaction events."""

from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.domain.entities import WalletTransactionEvent, WalletProvider, WalletEventType
from app.application.services.wallet_event_ingestion_service import WalletEventIngestionService


class IngestWalletEventUseCase:
    """Use case for ingesting wallet transaction events."""

    def __init__(self, service: WalletEventIngestionService):
        """Initialize use case.

        Args:
            service: Wallet event ingestion service
        """
        self.service = service

    async def execute(
        self,
        wallet_id: UUID,
        provider: WalletProvider,
        event_type: WalletEventType,
        amount: float,
        currency: str,
        occurred_at: datetime,
        provider_event_id: Optional[str] = None,
        metadata: Optional[dict] = None,
        idempotency_key: Optional[str] = None,
    ) -> WalletTransactionEvent:
        """Execute wallet event ingestion.

        Args:
            wallet_id: The wallet's unique identifier
            provider: The wallet provider
            event_type: The type of event
            amount: The transaction amount
            currency: The transaction currency
            occurred_at: When the event occurred
            provider_event_id: Optional provider's event ID for deduplication
            metadata: Optional event metadata
            idempotency_key: Optional idempotency key for duplicate prevention

        Returns:
            The ingested event
        """
        return await self.service.ingest_event(
            wallet_id=wallet_id,
            provider=provider,
            event_type=event_type,
            amount=amount,
            currency=currency,
            occurred_at=occurred_at,
            provider_event_id=provider_event_id,
            metadata=metadata,
            idempotency_key=idempotency_key,
        )


class ListWalletEventsUseCase:
    """Use case for listing wallet transaction events."""

    def __init__(self, service: WalletEventIngestionService):
        """Initialize use case.

        Args:
            service: Wallet event ingestion service
        """
        self.service = service

    async def execute(
        self,
        wallet_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> List[WalletTransactionEvent]:
        """Execute wallet event listing.

        Args:
            wallet_id: The wallet's unique identifier
            limit: Maximum number of events to return (default 100)
            offset: Number of events to skip (default 0)

        Returns:
            List of wallet transaction events
        """
        return await self.service.list_events(
            wallet_id=wallet_id,
            limit=limit,
            offset=offset,
        )
