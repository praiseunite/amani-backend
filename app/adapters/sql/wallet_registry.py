"""SQLAlchemy Core adapter for wallet registry.

Uses raw SQLAlchemy Core Table API for maximum control over constraint handling.
Raises IntegrityError on unique constraint violations for race condition handling.
"""

from typing import Optional
from uuid import UUID
from datetime import datetime

from sqlalchemy import Table, Column, String, Boolean, DateTime, BigInteger, JSON, select
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, ENUM
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import WalletRegistryEntry, WalletProvider
from app.ports.wallet_registry import WalletRegistryPort
from app.errors import DuplicateEntryError


class SQLWalletRegistry(WalletRegistryPort):
    """SQLAlchemy Core implementation of wallet registry port."""

    def __init__(self, session: AsyncSession, metadata):
        """Initialize SQL wallet registry.

        Args:
            session: Async SQLAlchemy session
            metadata: SQLAlchemy metadata for table reflection
        """
        self.session = session

        # Define the wallet_registry table using SQLAlchemy Core
        self.wallet_registry = Table(
            "wallet_registry",
            metadata,
            Column("id", BigInteger, primary_key=True, autoincrement=True),
            Column("external_id", PG_UUID(as_uuid=True), nullable=False, unique=True, index=True),
            Column("user_id", PG_UUID(as_uuid=True), nullable=False, index=True),
            Column(
                "provider",
                ENUM("fincra", "paystack", "flutterwave", name="wallet_provider"),
                nullable=False,
            ),
            Column("provider_account_id", String(255), nullable=False),
            Column("provider_customer_id", String(255), nullable=True),
            Column("idempotency_key", String(255), nullable=True, unique=True, index=True),
            Column("metadata", JSON, nullable=True),
            Column("is_active", Boolean, nullable=False, default=True),
            Column("created_at", DateTime, nullable=False),
            Column("updated_at", DateTime, nullable=False),
            extend_existing=True,
        )

    async def register(
        self, entry: WalletRegistryEntry, idempotency_key: Optional[str] = None
    ) -> WalletRegistryEntry:
        """Register a new wallet.

        Args:
            entry: The wallet registry entry to register
            idempotency_key: Optional idempotency key for duplicate prevention

        Returns:
            The registered wallet entry

        Raises:
            DuplicateEntryError: On unique constraint violations (for race condition handling)
        """
        now = datetime.utcnow()

        # Prepare insert values
        values = {
            "external_id": entry.id,
            "user_id": entry.user_id,
            "provider": entry.provider.value,
            "provider_account_id": entry.provider_account_id,
            "provider_customer_id": entry.provider_customer_id,
            "idempotency_key": idempotency_key,
            "metadata": entry.metadata,
            "is_active": entry.is_active,
            "created_at": now,
            "updated_at": now,
        }

        # Insert the record - may raise IntegrityError on constraint violation
        stmt = self.wallet_registry.insert().values(**values).returning(self.wallet_registry)

        try:
            result = await self.session.execute(stmt)
            await self.session.commit()
            row = result.fetchone()

            # Convert row to WalletRegistryEntry
            return self._row_to_entry(row)
        except IntegrityError as e:
            # Translate DB-specific IntegrityError to domain-level DuplicateEntryError
            # The original error with constraint details is preserved in __cause__
            await self.session.rollback()
            raise DuplicateEntryError(
                "Duplicate wallet registration detected (unique constraint violation)"
            ) from e

    async def get_by_provider(
        self, user_id: UUID, provider: WalletProvider
    ) -> Optional[WalletRegistryEntry]:
        """Get wallet by user ID and provider.

        Args:
            user_id: The user's unique identifier
            provider: The wallet provider

        Returns:
            Wallet registry entry if found, None otherwise
        """
        stmt = select(self.wallet_registry).where(
            self.wallet_registry.c.user_id == user_id,
            self.wallet_registry.c.provider == provider.value,
        )
        result = await self.session.execute(stmt)
        row = result.fetchone()

        if row is None:
            return None

        return self._row_to_entry(row)

    async def get_by_idempotency_key(self, idempotency_key: str) -> Optional[WalletRegistryEntry]:
        """Get wallet by idempotency key.

        Args:
            idempotency_key: The idempotency key

        Returns:
            Wallet registry entry if found, None otherwise
        """
        stmt = select(self.wallet_registry).where(
            self.wallet_registry.c.idempotency_key == idempotency_key
        )
        result = await self.session.execute(stmt)
        row = result.fetchone()

        if row is None:
            return None

        return self._row_to_entry(row)

    async def get_by_provider_wallet(
        self, user_id: UUID, provider: WalletProvider, provider_wallet_id: str
    ) -> Optional[WalletRegistryEntry]:
        """Get wallet by user ID, provider, and provider wallet ID.

        Args:
            user_id: The user's unique identifier
            provider: The wallet provider
            provider_wallet_id: The provider's wallet/account ID

        Returns:
            Wallet registry entry if found, None otherwise
        """
        stmt = select(self.wallet_registry).where(
            self.wallet_registry.c.user_id == user_id,
            self.wallet_registry.c.provider == provider.value,
            self.wallet_registry.c.provider_account_id == provider_wallet_id,
        )
        result = await self.session.execute(stmt)
        row = result.fetchone()

        if row is None:
            return None

        return self._row_to_entry(row)

    def _row_to_entry(self, row) -> WalletRegistryEntry:
        """Convert database row to WalletRegistryEntry.

        Args:
            row: Database row

        Returns:
            WalletRegistryEntry instance
        """
        # Use row._mapping for safe, consistent dict-like access across different DB drivers.
        # _mapping provides a stable interface that works with both sync and async results,
        # avoiding fragility from direct attribute access which varies by SQLAlchemy version.
        row_data = row._mapping
        return WalletRegistryEntry(
            id=row_data["external_id"],
            user_id=row_data["user_id"],
            provider=WalletProvider(row_data["provider"]),
            provider_account_id=row_data["provider_account_id"],
            provider_customer_id=row_data["provider_customer_id"],
            metadata=row_data["metadata"] or {},
            is_active=row_data["is_active"],
            created_at=row_data["created_at"],
            updated_at=row_data["updated_at"],
        )
