"""
User model for authentication and user management.
Includes support for Supabase Row-Level Security.
Uses integer primary key with UUID external_id for hexagonal architecture.
"""
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text, Enum as SQLEnum, BigInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import enum

from app.core.database import Base


class UserRole(str, enum.Enum):
    """User role enumeration for role-based access control."""
    ADMIN = "admin"
    CLIENT = "client"
    FREELANCER = "freelancer"


class User(Base):
    """
    User model for the Amani platform.
    Integrates with Supabase Auth and supports Row-Level Security.
    Uses integer primary key for internal operations and UUID for external APIs.
    """
    __tablename__ = "users"
    
    # Primary key - UUID for now (will be transitioned to integer in future migration)
    # This maintains backward compatibility with existing data
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    
    # Integer ID for internal operations (added in migration)
    integer_id = Column(BigInteger, unique=True, nullable=True, index=True)
    
    # User authentication and profile
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=True)
    phone_number = Column(String(50), nullable=True)
    
    # Password hash - only used if not using Supabase Auth
    hashed_password = Column(String(255), nullable=True)
    
    # User role for RBAC
    role = Column(SQLEnum(UserRole), default=UserRole.CLIENT, nullable=False)
    
    # User status
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    
    # OTP verification
    otp_code = Column(String(6), nullable=True)
    otp_expires_at = Column(DateTime, nullable=True)
    
    # Profile information
    avatar_url = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    projects_created = relationship("Project", back_populates="creator", foreign_keys="Project.creator_id")
    projects_as_buyer = relationship("Project", back_populates="buyer", foreign_keys="Project.buyer_id")
    projects_as_seller = relationship("Project", back_populates="seller", foreign_keys="Project.seller_id")
    transactions = relationship("Transaction", back_populates="user")
    kyc_records = relationship("Kyc", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, integer_id={self.integer_id}, email={self.email}, full_name={self.full_name})>"

