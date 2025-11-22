"""Wallet event ingestion service - orchestrates event ingestion with business rules."""

import logging
from typing import List, Optional
from uuid import UUID

from app.domain.entities import WalletEventType, WalletProvider, WalletTransactionEvent
from app.ports.audit import AuditPort
from app.ports.wallet_event_ingestion import WalletEventIngestionPort

logger = logging.getLogger(__name__)


class WalletEventIngestionService:
    """Service for ingesting wallet transaction events with idempotency and audit."""

    def __init__(
        self,
        event_ingestion_port: WalletEventIngestionPort,
        audit_port: AuditPort,
    ):
        """Initialize service.

        Args:
            event_ingestion_port: Port for event ingestion operations
            audit_port: Port for audit logging
        """
        self.event_ingestion_port = event_ingestion_port
        self.audit_port = audit_port

    async def ingest_event(
        self,
        wallet_id: UUID,
        provider: WalletProvider,
        event_type: WalletEventType,
        amount: float,
        currency: str,
        occurred_at,
        provider_event_id: Optional[str] = None,
        metadata: Optional[dict] = None,
        idempotency_key: Optional[str] = None,
    ) -> WalletTransactionEvent:
        """Ingest a wallet transaction event (idempotent).

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
        # Check for duplicate by provider_event_id first
        if provider_event_id:
            existing = await self.event_ingestion_port.get_by_provider_event_id(
                provider.value, provider_event_id
            )
            if existing:
                logger.info(
                    "Event ingestion duplicate (provider_event_id): wallet_id=%s, provider=%s, provider_event_id=%s",
                    str(wallet_id),
                    provider.value,
                    provider_event_id,
                )
                return existing

        # Check for duplicate by idempotency_key
        if idempotency_key:
            # Note: We rely on the port to handle this check during ingest
            pass

        # Create the event
        event = WalletTransactionEvent(
            wallet_id=wallet_id,
            provider=provider,
            event_type=event_type,
            amount=amount,
            currency=currency,
            provider_event_id=provider_event_id,
            metadata=metadata or {},
            occurred_at=occurred_at,
        )

        # Ingest the event (idempotent)
        ingested = await self.event_ingestion_port.ingest_event(event, idempotency_key)

        # Log audit event only if this is a new ingestion (not duplicate)
        if ingested.id == event.id:
            await self.audit_port.record(
                user_id=None,  # System action - wallet event ingestion
                action="ingest_wallet_event",
                resource_type="wallet_transaction_event",
                resource_id=str(ingested.id),
                details={
                    "wallet_id": str(wallet_id),
                    "provider": provider.value,
                    "event_type": event_type.value,
                    "amount": amount,
                    "currency": currency,
                    "provider_event_id": provider_event_id,
                    "occurred_at": occurred_at.isoformat(),
                },
            )
            logger.info(
                "Event ingestion success: event_id=%s, wallet_id=%s, provider=%s, event_type=%s",
                str(ingested.id),
                str(wallet_id),
                provider.value,
                event_type.value,
            )

        return ingested

    async def get_event(self, event_id: UUID) -> Optional[WalletTransactionEvent]:
        """Get an event by ID.

        Args:
            event_id: The event's unique identifier

        Returns:
            The event if found, None otherwise
        """
        return await self.event_ingestion_port.get_by_event_id(event_id)

    async def list_events(
        self,
        wallet_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> List[WalletTransactionEvent]:
        """List events for a wallet.

        Args:
            wallet_id: The wallet's unique identifier
            limit: Maximum number of events to return (default 100)
            offset: Number of events to skip (default 0)

        Returns:
            List of wallet transaction events ordered by occurred_at descending
        """
        return await self.event_ingestion_port.list_by_wallet_id(
            wallet_id, limit=limit, offset=offset
        )
