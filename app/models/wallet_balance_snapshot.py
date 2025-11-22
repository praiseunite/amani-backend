"""
WalletBalanceSnapshot model for tracking wallet balances over time.
Uses integer primary key with UUID external_id for hexagonal architecture.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum, BigInteger, JSON, Numeric
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.core.database import Base
from app.models.link_token import WalletProvider


class WalletBalanceSnapshot(Base):
    """
    WalletBalanceSnapshot model for tracking wallet balance snapshots.
    Uses integer primary key for internal operations and UUID for external APIs.
    """

    __tablename__ = "wallet_balance_snapshot"

    # Primary key - integer bigserial for performance
    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)

    # External UUID for API compatibility
    external_id = Column(
        UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4, index=True
    )

    # Wallet reference (UUID from wallet_registry)
    wallet_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Provider information
    provider = Column(SQLEnum(WalletProvider), nullable=False, index=True)

    # Balance information
    balance = Column(Numeric(precision=20, scale=2), nullable=False)
    currency = Column(String(3), nullable=False, default="USD")

    # External balance/event ID from provider (for idempotency)
    external_balance_id = Column(String(255), nullable=True, unique=True, index=True)

    # Timestamp of the balance snapshot
    as_of = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Additional metadata (using 'extra_data' to avoid SQLAlchemy's reserved 'metadata')
    extra_data = Column("metadata", JSON, nullable=True, default=dict)

    # Idempotency key for duplicate prevention
    idempotency_key = Column(String(255), nullable=True, unique=True, index=True)

    # Creation timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<WalletBalanceSnapshot(id={self.id}, wallet_id={self.wallet_id}, balance={self.balance})>"
