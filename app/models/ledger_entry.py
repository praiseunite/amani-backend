"""
LedgerEntry model for accounting entries.
Uses integer primary key with UUID external_id for hexagonal architecture.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Column, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class TransactionType(str, enum.Enum):
    """Type of ledger transaction."""

    DEBIT = "debit"
    CREDIT = "credit"


class LedgerEntry(Base):
    """
    LedgerEntry model for accounting purposes.
    Uses integer primary key for internal operations and UUID for external APIs.
    """

    __tablename__ = "ledger_entries"

    # Primary key - integer bigserial for performance
    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)

    # External UUID for API compatibility
    external_id = Column(
        UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4, index=True
    )

    # User reference (will be migrated to integer FK in future)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Transaction details
    transaction_type = Column(SQLEnum(TransactionType), nullable=False)
    amount = Column(Numeric(precision=15, scale=2), nullable=False)
    currency = Column(String(3), nullable=False, default="USD")
    balance_after = Column(Numeric(precision=15, scale=2), nullable=False)

    # Reference and description
    reference = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self):
        return f"<LedgerEntry(id={self.id}, external_id={self.external_id}, type={self.transaction_type}, amount={self.amount})>"
