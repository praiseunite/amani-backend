"""
Project model for escrow projects.
Supports Row-Level Security for Supabase.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class ProjectStatus(str, enum.Enum):
    """Project status enumeration."""

    DRAFT = "draft"
    PENDING = "pending"
    ACTIVE = "active"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DISPUTED = "disputed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class Project(Base):
    """
    Project model representing an escrow agreement.
    Tracks the transaction between buyer and seller.
    """

    __tablename__ = "projects"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)

    # Project details
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)

    # Financial information
    total_amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default="USD", nullable=False)

    # Project status
    status = Column(
        Enum(ProjectStatus, name="project_status", create_type=True),
        default=ProjectStatus.DRAFT,
        nullable=False,
        index=True,
    )

    # Participants - Foreign Keys to User
    creator_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    buyer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    seller_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)

    # Terms and conditions
    terms_accepted_at = Column(DateTime, nullable=True)
    completion_criteria = Column(Text, nullable=True)

    # Deadlines
    start_date = Column(DateTime, nullable=True)
    due_date = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    creator = relationship("User", back_populates="projects_created", foreign_keys=[creator_id])
    buyer = relationship("User", back_populates="projects_as_buyer", foreign_keys=[buyer_id])
    seller = relationship("User", back_populates="projects_as_seller", foreign_keys=[seller_id])
    milestones = relationship("Milestone", back_populates="project", cascade="all, delete-orphan")
    transactions = relationship(
        "Transaction", back_populates="project", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Project(id={self.id}, title={self.title}, status={self.status})>"
