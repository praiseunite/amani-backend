"""
WalletBalanceSnapshot model for tracking wallet balances over time.
Uses integer primary key with UUID external_id for hexagonal architecture.
"""

import uuid
from datetime import datetime

from sqlalchemy import JSON, BigInteger, Column, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base
from app.models.link_token import WalletProvider


class WalletBalanceSnapshot(Base):
    """
    WalletBalanceSnapshot model for tracking wallet balance snapshots.
    Uses integer primary key for internal operations and UUID for external APIs.
    """

    __tablename__ = "wallet_balance_snapshot"

    # Primary key - UUID for API and internal operations
    id = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False, index=True
    )

    wallet_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    provider = Column(SQLEnum(WalletProvider), nullable=False, index=True)
    balance = Column(Numeric(precision=20, scale=2), nullable=False)
    currency = Column(String(3), nullable=False, default="USD")
    external_balance_id = Column(String(255), nullable=True, unique=True, index=True)
    as_of = Column(DateTime, nullable=False, default=datetime.utcnow)
    extra_data = Column("metadata", JSON, nullable=True, default=dict)
    idempotency_key = Column(String(255), nullable=True, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<WalletBalanceSnapshot(id={self.id}, wallet_id={self.wallet_id}, balance={self.balance})>"
