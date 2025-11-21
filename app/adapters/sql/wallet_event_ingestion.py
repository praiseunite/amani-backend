"""SQLAlchemy Core adapter for wallet event ingestion.

Uses raw SQLAlchemy Core Table API for maximum control over constraint handling.
Raises DuplicateEntryError on unique constraint violations for race condition handling.
"""

from typing import List, Optional
from uuid import UUID
from datetime import datetime

from sqlalchemy import Table, Column, String, Float, DateTime, BigInteger, JSON, select
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, ENUM
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import WalletTransactionEvent, WalletProvider, WalletEventType
from app.ports.wallet_event_ingestion import WalletEventIngestionPort
from app.errors import DuplicateEntryError


class SQLWalletEventIngestion(WalletEventIngestionPort):
    """SQLAlchemy Core implementation of wallet event ingestion port."""

    def __init__(self, session: AsyncSession, metadata):
        """Initialize SQL wallet event ingestion.

        Args:
            session: Async SQLAlchemy session
            metadata: SQLAlchemy metadata for table reflection
        """
        self.session = session

        # Define the wallet_transaction_event table using SQLAlchemy Core
        self.wallet_transaction_event = Table(
            "wallet_transaction_event",
            metadata,
            Column("id", BigInteger, primary_key=True, autoincrement=True),
            Column("external_id", PG_UUID(as_uuid=True), nullable=False, unique=True, index=True),
            Column("wallet_id", PG_UUID(as_uuid=True), nullable=False, index=True),
            Column(
                "provider",
                ENUM("fincra", "paystack", "flutterwave", name="wallet_provider"),
                nullable=False,
            ),
            Column(
                "event_type",
                ENUM(
                    "deposit",
                    "withdrawal",
                    "transfer_in",
                    "transfer_out",
                    "fee",
                    "refund",
                    "hold",
                    "release",
                    name="wallet_event_type",
                ),
                nullable=False,
            ),
            Column("amount", Float, nullable=False),
            Column("currency", String(10), nullable=False),
            Column("provider_event_id", String(255), nullable=True, index=True),
            Column("idempotency_key", String(255), nullable=True, unique=True, index=True),
            Column("metadata", JSON, nullable=True),
            Column("occurred_at", DateTime, nullable=False, index=True),
            Column("created_at", DateTime, nullable=False),
            extend_existing=True,
        )

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
            DuplicateEntryError: On unique constraint violations (for race condition handling)
        """
        # First check for existing event by external_id
        existing = await self.get_by_event_id(event.id)
        if existing:
            return existing

        # Check for existing event by provider_event_id
        if event.provider_event_id:
            existing_provider = await self.get_by_provider_event_id(
                event.provider.value, event.provider_event_id
            )
            if existing_provider:
                return existing_provider

        now = datetime.utcnow()

        # Prepare insert values
        values = {
            "external_id": event.id,
            "wallet_id": event.wallet_id,
            "provider": event.provider.value,
            "event_type": event.event_type.value,
            "amount": event.amount,
            "currency": event.currency,
            "provider_event_id": event.provider_event_id,
            "idempotency_key": idempotency_key,
            "metadata": event.metadata,
            "occurred_at": event.occurred_at,
            "created_at": now,
        }

        # Insert the record - may raise IntegrityError on constraint violation
        stmt = (
            self.wallet_transaction_event.insert()
            .values(**values)
            .returning(self.wallet_transaction_event)
        )

        try:
            result = await self.session.execute(stmt)
            await self.session.commit()
            row = result.fetchone()

            # Convert row to WalletTransactionEvent
            return self._row_to_event(row)
        except IntegrityError as e:
            # Translate DB-specific IntegrityError to domain-level DuplicateEntryError
            # The original error with constraint details is preserved in __cause__
            await self.session.rollback()
            raise DuplicateEntryError(
                "Duplicate event ingestion detected (unique constraint violation)"
            ) from e

    async def get_by_event_id(self, event_id: UUID) -> Optional[WalletTransactionEvent]:
        """Get event by event ID.

        Args:
            event_id: The event's unique identifier

        Returns:
            Wallet transaction event if found, None otherwise
        """
        stmt = select(self.wallet_transaction_event).where(
            self.wallet_transaction_event.c.external_id == event_id
        )
        result = await self.session.execute(stmt)
        row = result.fetchone()

        if row is None:
            return None

        return self._row_to_event(row)

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
        stmt = (
            select(self.wallet_transaction_event)
            .where(self.wallet_transaction_event.c.wallet_id == wallet_id)
            .order_by(self.wallet_transaction_event.c.occurred_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        rows = result.fetchall()

        return [self._row_to_event(row) for row in rows]

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
        stmt = select(self.wallet_transaction_event).where(
            self.wallet_transaction_event.c.provider == provider,
            self.wallet_transaction_event.c.provider_event_id == provider_event_id,
        )
        result = await self.session.execute(stmt)
        row = result.fetchone()

        if row is None:
            return None

        return self._row_to_event(row)

    def _row_to_event(self, row) -> WalletTransactionEvent:
        """Convert database row to WalletTransactionEvent.

        Args:
            row: Database row

        Returns:
            WalletTransactionEvent instance
        """
        row_data = row._mapping
        return WalletTransactionEvent(
            id=row_data["external_id"],
            wallet_id=row_data["wallet_id"],
            provider=WalletProvider(row_data["provider"]),
            event_type=WalletEventType(row_data["event_type"]),
            amount=row_data["amount"],
            currency=row_data["currency"],
            provider_event_id=row_data["provider_event_id"],
            metadata=row_data["metadata"] or {},
            occurred_at=row_data["occurred_at"],
            created_at=row_data["created_at"],
        )
