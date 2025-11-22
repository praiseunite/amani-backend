"""
KYC (Know Your Customer) model for identity verification.
Supports both KYC (individuals) and KYB (businesses).
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, LargeBinary, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class KycType(str, enum.Enum):
    """KYC type enumeration."""

    KYC = "kyc"  # Know Your Customer (individuals)
    KYB = "kyb"  # Know Your Business (businesses)


class KycStatus(str, enum.Enum):
    """KYC status enumeration."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class Kyc(Base):
    """
    KYC model for identity verification in the Amani platform.
    Stores KYC/KYB documents and verification status.
    """

    __tablename__ = "kyc"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)

    # Foreign key to User
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    # KYC type (individual or business)
    type = Column(SQLEnum(KycType), nullable=False, default=KycType.KYC)

    # Identity information
    nin_or_passport = Column(String(100), nullable=False, index=True)

    # Biometric data (stored as binary)
    fingerprint = Column(LargeBinary, nullable=True)

    # Security codes (should be hashed before storage)
    security_code = Column(String(255), nullable=False)
    approval_code = Column(String(255), nullable=True)  # For clients

    # Identity document image (stored as binary)
    image = Column(LargeBinary, nullable=True)

    # Verification status
    status = Column(SQLEnum(KycStatus), nullable=False, default=KycStatus.PENDING, index=True)

    # Rejection information
    rejection_reason = Column(Text, nullable=True)

    # Timestamps
    submitted_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    verified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="kyc_records")

    def __repr__(self):
        return (
            f"<Kyc(id={self.id}, user_id={self.user_id}, type={self.type}, status={self.status})>"
        )
