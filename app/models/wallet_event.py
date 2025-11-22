"""
WalletTransactionEvent model for tracking wallet transaction events.
Uses integer primary key with UUID external_id for hexagonal architecture.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Enum as SQLEnum, BigInteger, JSON
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.core.database import Base
from app.models.link_token import WalletProvider


class WalletEventType(str, SQLEnum):
    """Type of wallet transaction event."""

    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSFER_IN = "transfer_in"
    TRANSFER_OUT = "transfer_out"
    FEE = "fee"
    REFUND = "refund"
    HOLD = "hold"
    RELEASE = "release"


class WalletTransactionEvent(Base):
    """
    WalletTransactionEvent model for tracking wallet transaction events.
    Uses integer primary key for internal operations and UUID for external APIs.
    """

    __tablename__ = "wallet_transaction_event"

    # Primary key - integer bigserial for performance
    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)

    # External UUID for API compatibility
    external_id = Column(
        UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4, index=True
    )

    # Wallet reference
    wallet_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Provider information
    provider = Column(SQLEnum(WalletProvider), nullable=False)

    # Event details
    event_type = Column(
        SQLEnum(
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
    )
    amount = Column(Float, nullable=False)
    currency = Column(String(10), nullable=False, default="USD")
    provider_event_id = Column(String(255), nullable=True, index=True)

    # Additional metadata (using 'extra_data' to avoid SQLAlchemy's reserved 'metadata')
    extra_data = Column("metadata", JSON, nullable=True, default=dict)

    # Idempotency
    idempotency_key = Column(String(255), nullable=True, unique=True, index=True)

    # Timestamps
    occurred_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<WalletTransactionEvent(id={self.id}, external_id={self.external_id}, event_type={self.event_type})>"
