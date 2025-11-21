"""In-memory wallet event ingestion implementation for testing."""

from typing import Dict, List, Optional
from uuid import UUID

from app.domain.entities import WalletTransactionEvent
from app.ports.wallet_event_ingestion import WalletEventIngestionPort


class InMemoryWalletEventIngestion(WalletEventIngestionPort):
    """In-memory implementation of wallet event ingestion port."""

    def __init__(self):
        """Initialize in-memory storage."""
        self._events: List[WalletTransactionEvent] = []
        self._idempotency_keys: Dict[str, WalletTransactionEvent] = {}

    async def ingest_event(
        self, event: WalletTransactionEvent, idempotency_key: Optional[str] = None
    ) -> WalletTransactionEvent:
        """Ingest a wallet transaction event (idempotent).

        Args:
            event: The wallet transaction event to ingest
            idempotency_key: Optional idempotency key for duplicate prevention

        Returns:
            The ingested event

        Raises:
            DuplicateEntryError: If event with same event_id or provider_event_id exists
        """
        # Check for duplicate event_id
        existing = await self.get_by_event_id(event.id)
        if existing:
            return existing

        # Check for duplicate provider_event_id
        if event.provider_event_id:
            existing_provider = await self.get_by_provider_event_id(
                event.provider.value, event.provider_event_id
            )
            if existing_provider:
                return existing_provider

        # Check for duplicate idempotency_key
        if idempotency_key:
            if idempotency_key in self._idempotency_keys:
                return self._idempotency_keys[idempotency_key]

        # Store the event
        self._events.append(event)
        if idempotency_key:
            self._idempotency_keys[idempotency_key] = event

        return event

    async def get_by_event_id(self, event_id: UUID) -> Optional[WalletTransactionEvent]:
        """Get event by event ID.

        Args:
            event_id: The event's unique identifier

        Returns:
            Wallet transaction event if found, None otherwise
        """
        for event in self._events:
            if event.id == event_id:
                return event
        return None

    async def list_by_wallet_id(
        self,
        wallet_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> List[WalletTransactionEvent]:
        """List events for a wallet, ordered by occurred_at descending.

        Args:
            wallet_id: The wallet's unique identifier
            limit: Maximum number of events to return (default 100)
            offset: Number of events to skip (default 0)

        Returns:
            List of wallet transaction events
        """
        # Filter by wallet_id
        wallet_events = [event for event in self._events if event.wallet_id == wallet_id]

        # Sort by occurred_at descending
        wallet_events.sort(key=lambda e: e.occurred_at, reverse=True)

        # Apply offset and limit
        return wallet_events[offset : offset + limit]

    async def get_by_provider_event_id(
        self, provider: str, provider_event_id: str
    ) -> Optional[WalletTransactionEvent]:
        """Get event by provider and provider event ID.

        Args:
            provider: The wallet provider
            provider_event_id: The provider's event ID

        Returns:
            Wallet transaction event if found, None otherwise
        """
        for event in self._events:
            if event.provider.value == provider and event.provider_event_id == provider_event_id:
                return event
        return None
