"""
Transaction model for tracking all financial transactions.
Supports Row-Level Security for Supabase.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class TransactionType(str, enum.Enum):
    """Transaction type enumeration."""

    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    ESCROW_HOLD = "escrow_hold"
    ESCROW_RELEASE = "escrow_release"
    REFUND = "refund"
    FEE = "fee"
    COMMISSION = "commission"


class TransactionStatus(str, enum.Enum):
    """Transaction status enumeration."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class Transaction(Base):
    """
    Transaction model for all financial operations in the platform.
    Integrates with FinCra payment gateway.
    """

    __tablename__ = "transactions"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)

    # Foreign keys
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Transaction details
    transaction_type = Column(
        Enum(TransactionType, name="transaction_type", create_type=True), nullable=False, index=True
    )
    status = Column(
        Enum(TransactionStatus, name="transaction_status", create_type=True),
        default=TransactionStatus.PENDING,
        nullable=False,
        index=True,
    )

    # Financial information
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default="USD", nullable=False)
    fee = Column(Numeric(15, 2), default=0, nullable=False)
    net_amount = Column(Numeric(15, 2), nullable=False)

    # Payment gateway information
    payment_gateway = Column(String(50), default="fincra", nullable=True)
    gateway_transaction_id = Column(String(255), nullable=True, unique=True, index=True)
    gateway_reference = Column(String(255), nullable=True)
    gateway_response = Column(JSON, nullable=True)

    # Transaction metadata
    description = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    extra_data = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="transactions")
    project = relationship("Project", back_populates="transactions")

    def __repr__(self):
        return f"<Transaction(id={self.id}, type={self.transaction_type}, status={self.status}, amount={self.amount})>"
