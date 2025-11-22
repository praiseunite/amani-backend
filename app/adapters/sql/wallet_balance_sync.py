"""SQLAlchemy Core adapter for wallet balance sync.

Uses raw SQLAlchemy Core Table API for maximum control over constraint handling.
Raises DuplicateEntryError on unique constraint violations for race condition handling.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import JSON, BigInteger, Column, DateTime, Numeric, String, Table, select
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import WalletBalanceSnapshot, WalletProvider
from app.errors import DuplicateEntryError
from app.ports.wallet_balance_sync import WalletBalanceSyncPort


class SQLWalletBalanceSync(WalletBalanceSyncPort):
    """SQLAlchemy Core implementation of wallet balance sync port."""

    def __init__(self, session: AsyncSession, metadata):
        """Initialize SQL wallet balance sync.

        Args:
            session: Async SQLAlchemy session
            metadata: SQLAlchemy metadata for table reflection
        """
        self.session = session

        # Define the wallet_balance_snapshot table using SQLAlchemy Core
        self.wallet_balance_snapshot = Table(
            "wallet_balance_snapshot",
            metadata,
            Column("id", PG_UUID(as_uuid=True), primary_key=True, nullable=False, index=True),
            Column("wallet_id", PG_UUID(as_uuid=True), nullable=False, index=True),
            Column(
                "provider",
                ENUM("fincra", "paystack", "flutterwave", name="wallet_provider"),
                nullable=False,
            ),
            Column("balance", Numeric(precision=20, scale=2), nullable=False),
            Column("currency", String(3), nullable=False),
            Column("external_balance_id", String(255), nullable=True, index=True),
            Column("as_of", DateTime, nullable=False),
            Column("metadata", JSON, nullable=True),
            Column("idempotency_key", String(255), nullable=True, unique=True, index=True),
            Column("created_at", DateTime, nullable=False),
            extend_existing=True,
        )

    async def get_latest(self, wallet_id: UUID) -> Optional[WalletBalanceSnapshot]:
        """Get the latest balance snapshot for a wallet.

        Args:
            wallet_id: The wallet's unique identifier

        Returns:
            Latest balance snapshot if found, None otherwise
        """
        stmt = (
            select(self.wallet_balance_snapshot)
            .where(self.wallet_balance_snapshot.c.wallet_id == wallet_id)
            .order_by(self.wallet_balance_snapshot.c.as_of.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        row = result.fetchone()

        if row is None:
            return None

        return self._row_to_snapshot(row)

    async def get_by_external_id(self, external_balance_id: str) -> Optional[WalletBalanceSnapshot]:
        """Get balance snapshot by external provider event ID.

        Args:
            external_balance_id: The provider's balance event/snapshot ID

        Returns:
            Balance snapshot if found, None otherwise
        """
        stmt = select(self.wallet_balance_snapshot).where(
            self.wallet_balance_snapshot.c.external_balance_id == external_balance_id
        )
        result = await self.session.execute(stmt)
        row = result.fetchone()

        if row is None:
            return None

        return self._row_to_snapshot(row)

    async def save_snapshot(
        self, snapshot: WalletBalanceSnapshot, idempotency_key: Optional[str] = None
    ) -> WalletBalanceSnapshot:
        """Save a balance snapshot.

        Args:
            snapshot: The balance snapshot to save
            idempotency_key: Optional idempotency key for duplicate prevention

        Returns:
            The saved snapshot

        Raises:
            DuplicateEntryError: On unique constraint violations
        """
        now = datetime.utcnow()

        # Prepare insert values
        values = {
            "id": snapshot.id,
            "wallet_id": snapshot.wallet_id,
            "provider": snapshot.provider.value,
            "balance": snapshot.balance,
            "currency": snapshot.currency,
            "external_balance_id": snapshot.external_balance_id,
            "as_of": snapshot.as_of,
            "metadata": snapshot.metadata,
            "idempotency_key": idempotency_key,
            "created_at": now,
        }

        # Insert the record - may raise IntegrityError on constraint violation
        stmt = (
            self.wallet_balance_snapshot.insert()
            .values(**values)
            .returning(self.wallet_balance_snapshot)
        )

        try:
            result = await self.session.execute(stmt)
            await self.session.commit()
            row = result.fetchone()

            # Convert row to WalletBalanceSnapshot
            return self._row_to_snapshot(row)
        except IntegrityError as e:
            # Translate DB-specific IntegrityError to domain-level DuplicateEntryError
            await self.session.rollback()
            raise DuplicateEntryError(
                "Duplicate balance snapshot detected (unique constraint violation)"
            ) from e

    async def get_by_idempotency_key(self, idempotency_key: str) -> Optional[WalletBalanceSnapshot]:
        """Get snapshot by idempotency key.

        Args:
            idempotency_key: The idempotency key

        Returns:
            Balance snapshot if found, None otherwise
        """
        stmt = select(self.wallet_balance_snapshot).where(
            self.wallet_balance_snapshot.c.idempotency_key == idempotency_key
        )
        result = await self.session.execute(stmt)
        row = result.fetchone()

        if row is None:
            return None

        return self._row_to_snapshot(row)

    def _row_to_snapshot(self, row) -> WalletBalanceSnapshot:
        """Convert database row to WalletBalanceSnapshot.

        Args:
            row: Database row

        Returns:
            WalletBalanceSnapshot instance
        """
        row_data = row._mapping
        return WalletBalanceSnapshot(
            id=row_data["id"],
            wallet_id=row_data["wallet_id"],
            provider=WalletProvider(row_data["provider"]),
            balance=float(row_data["balance"]),
            currency=row_data["currency"],
            external_balance_id=row_data["external_balance_id"],
            as_of=row_data["as_of"],
            metadata=row_data["metadata"] or {},
            created_at=row_data["created_at"],
        )
