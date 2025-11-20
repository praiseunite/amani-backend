"""
SQLAlchemy adapter for wallet_registry
"""
from typing import Optional, Dict, Any
import json
import logging

from sqlalchemy import Table, Column, Integer, String, JSON, MetaData, UniqueConstraint
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import select
from sqlalchemy.engine import Engine

from app.ports.wallet_registry import WalletRegistryPort, WalletRegistryRecord

logger = logging.getLogger(__name__)
metadata = MetaData()

wallet_registry_table = Table(
    "wallet_registry",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("provider", String(64), nullable=False),
    Column("provider_wallet_id", String(255), nullable=False),
    Column("bot_user_id", String(128), nullable=True),
    Column("metadata", JSON, nullable=True),
    Column("idempotency_key", String(255), nullable=True, unique=True),
    UniqueConstraint("provider", "provider_wallet_id", name="uq_provider_wallet"),
)


class SQLWalletRegistryAdapter(WalletRegistryPort):
    def __init__(self, engine: Engine):
        self.engine = engine

    def _row_to_record(self, row) -> WalletRegistryRecord:
        return WalletRegistryRecord(
            id=row["id"],
            provider=row["provider"],
            provider_wallet_id=row["provider_wallet_id"],
            bot_user_id=row.get("bot_user_id"),
            metadata=row.get("metadata") or {},
            idempotency_key=row.get("idempotency_key"),
        )

    def create(self, provider: str, provider_wallet_id: str, bot_user_id: Optional[str], metadata: Optional[Dict[str, Any]] = None, idempotency_key: Optional[str] = None) -> WalletRegistryRecord:
        ins = wallet_registry_table.insert().values(
            provider=provider,
            provider_wallet_id=provider_wallet_id,
            bot_user_id=bot_user_id,
            metadata=metadata or {},
            idempotency_key=idempotency_key,
        )
        with self.engine.begin() as conn:
            try:
                result = conn.execute(ins)
                rowid = result.inserted_primary_key[0]
                sel = select([wallet_registry_table]).where(wallet_registry_table.c.id == rowid)
                row = conn.execute(sel).fetchone()
                return self._row_to_record(row)
            except IntegrityError as exc:
                logger.debug("IntegrityError during create: %s", exc)
                # propagate so service can resolve race
                raise

    def get_by_idempotency_key(self, idempotency_key: str) -> Optional[WalletRegistryRecord]:
        sel = select([wallet_registry_table]).where(wallet_registry_table.c.idempotency_key == idempotency_key)
        with self.engine.begin() as conn:
            row = conn.execute(sel).fetchone()
            if row:
                return self._row_to_record(row)
        return None

    def get_by_provider(self, provider: str, provider_wallet_id: str) -> Optional[WalletRegistryRecord]:
        sel = select([wallet_registry_table]).where(
            (wallet_registry_table.c.provider == provider) & (wallet_registry_table.c.provider_wallet_id == provider_wallet_id)
        )
        with self.engine.begin() as conn:
            row = conn.execute(sel).fetchone()
            if row:
                return self._row_to_record(row)
        return None
