"""Wallet event ingestion port - interface for wallet transaction event operations."""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from app.domain.entities import WalletTransactionEvent


class WalletEventIngestionPort(ABC):
    """Port for wallet transaction event ingestion operations."""

    @abstractmethod
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
        pass

    @abstractmethod
    async def get_by_event_id(self, event_id: UUID) -> Optional[WalletTransactionEvent]:
        """Get event by event ID.

        Args:
            event_id: The event's unique identifier

        Returns:
            Wallet transaction event if found, None otherwise
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass
