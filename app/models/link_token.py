"""
LinkToken model for wallet connection tokens.
Uses integer primary key with UUID external_id for hexagonal architecture.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum as SQLEnum, BigInteger
from sqlalchemy.dialects.postgresql import UUID
import uuid
import enum

from app.core.database import Base


class WalletProvider(str, enum.Enum):
    """Supported wallet providers."""

    FINCRA = "fincra"
    PAYSTACK = "paystack"
    FLUTTERWAVE = "flutterwave"


class LinkToken(Base):
    """
    LinkToken model for connecting external wallets.
    Uses integer primary key for internal operations and UUID for external APIs.
    """

    __tablename__ = "link_tokens"

    # Primary key - integer bigserial for performance
    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)

    # External UUID for API compatibility
    external_id = Column(
        UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4, index=True
    )

    # User reference (will be migrated to integer FK in future)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Token properties
    token = Column(String(255), unique=True, nullable=False, index=True)
    provider = Column(SQLEnum(WalletProvider), nullable=False)

    # Token status
    is_consumed = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    consumed_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return (
            f"<LinkToken(id={self.id}, external_id={self.external_id}, token={self.token[:10]}...)>"
        )
