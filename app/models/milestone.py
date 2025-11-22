"""
Milestone model for tracking project progress.
Supports Row-Level Security for Supabase.
"""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Enum, Numeric, ForeignKey, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import enum

from app.core.database import Base


class MilestoneStatus(str, enum.Enum):
    """Milestone status enumeration."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    APPROVED = "approved"
    REJECTED = "rejected"
    DISPUTED = "disputed"


class Milestone(Base):
    """
    Milestone model for breaking down projects into smaller deliverables.
    Each milestone has its own payment amount and completion criteria.
    """

    __tablename__ = "milestones"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)

    # Foreign key to project
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Milestone details
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    order_index = Column(Integer, nullable=False, default=0)

    # Financial information
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default="USD", nullable=False)

    # Status
    status = Column(
        Enum(MilestoneStatus, name="milestone_status", create_type=True),
        default=MilestoneStatus.PENDING,
        nullable=False,
        index=True,
    )

    # Completion tracking
    is_paid = Column(Boolean, default=False, nullable=False)
    completion_criteria = Column(Text, nullable=True)
    completion_notes = Column(Text, nullable=True)

    # Deadlines
    due_date = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    paid_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    project = relationship("Project", back_populates="milestones")

    def __repr__(self):
        return f"<Milestone(id={self.id}, title={self.title}, status={self.status}, amount={self.amount})>"
