"""
Hold model for escrow fund holds.
Uses integer primary key with UUID external_id for hexagonal architecture.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum, BigInteger, Numeric
from sqlalchemy.dialects.postgresql import UUID
import uuid
import enum

from app.core.database import Base


class HoldStatus(str, enum.Enum):
    """Status of a hold on funds."""

    ACTIVE = "active"
    RELEASED = "released"
    CAPTURED = "captured"


class Hold(Base):
    """
    Hold model for escrow fund holds.
    Uses integer primary key for internal operations and UUID for external APIs.
    """

    __tablename__ = "holds"

    # Primary key - integer bigserial for performance
    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)

    # External UUID for API compatibility
    external_id = Column(
        UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4, index=True
    )

    # User reference (will be migrated to integer FK in future)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Amount information
    amount = Column(Numeric(precision=15, scale=2), nullable=False)
    currency = Column(String(3), nullable=False, default="USD")

    # Hold details
    status = Column(SQLEnum(HoldStatus), nullable=False, default=HoldStatus.ACTIVE)
    reference = Column(String(255), nullable=False, unique=True, index=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    released_at = Column(DateTime, nullable=True)
    captured_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<Hold(id={self.id}, external_id={self.external_id}, amount={self.amount}, status={self.status})>"
