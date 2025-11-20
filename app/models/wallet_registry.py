"""
WalletRegistry model for connected wallet entries.
Uses integer primary key with UUID external_id for hexagonal architecture.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum as SQLEnum, BigInteger, JSON
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.core.database import Base
from app.models.link_token import WalletProvider


class WalletRegistry(Base):
    """
    WalletRegistry model for tracking connected wallets.
    Uses integer primary key for internal operations and UUID for external APIs.
    """
    __tablename__ = "wallet_registry"
    
    # Primary key - integer bigserial for performance
    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    
    # External UUID for API compatibility
    external_id = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4, index=True)
    
    # User reference (will be migrated to integer FK in future)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Provider information
    provider = Column(SQLEnum(WalletProvider), nullable=False)
    provider_account_id = Column(String(255), nullable=False)
    provider_customer_id = Column(String(255), nullable=True)
    
    # Additional metadata (using 'extra_data' to avoid SQLAlchemy's reserved 'metadata')
    extra_data = Column('metadata', JSON, nullable=True, default=dict)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<WalletRegistry(id={self.id}, external_id={self.external_id}, provider={self.provider})>"

