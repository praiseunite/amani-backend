"""
User model for authentication and user management.
Includes support for Supabase Row-Level Security.
"""
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base


class User(Base):
    """
    User model for the Amani platform.
    Integrates with Supabase Auth and supports Row-Level Security.
    """
    __tablename__ = "users"
    
    # Primary key - use UUID for Supabase compatibility
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    
    # User authentication and profile
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=True)
    phone_number = Column(String(50), nullable=True)
    
    # Password hash - only used if not using Supabase Auth
    hashed_password = Column(String(255), nullable=True)
    
    # User status
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    
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
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, full_name={self.full_name})>"
