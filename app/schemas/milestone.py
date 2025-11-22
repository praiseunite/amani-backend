"""
Pydantic schemas for milestone operations.
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.milestone import MilestoneStatus


class MilestoneBase(BaseModel):
    """Base milestone schema with common fields."""

    title: str = Field(..., min_length=3, max_length=255)
    description: str = Field(..., min_length=10)
    amount: Decimal = Field(..., gt=0)
    currency: str = Field(default="USD", pattern="^[A-Z]{3}$")
    completion_criteria: Optional[str] = None
    due_date: Optional[datetime] = None
    order_index: int = Field(default=0, ge=0)


class MilestoneCreate(MilestoneBase):
    """Schema for creating a new milestone."""

    project_id: UUID


class MilestoneUpdate(BaseModel):
    """Schema for updating a milestone."""

    title: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = Field(None, min_length=10)
    amount: Optional[Decimal] = Field(None, gt=0)
    currency: Optional[str] = Field(None, pattern="^[A-Z]{3}$")
    completion_criteria: Optional[str] = None
    due_date: Optional[datetime] = None
    order_index: Optional[int] = Field(None, ge=0)
    status: Optional[MilestoneStatus] = None


class MilestoneSubmit(BaseModel):
    """Schema for submitting a milestone for approval."""

    completion_notes: Optional[str] = None


class MilestoneApprove(BaseModel):
    """Schema for approving or rejecting a milestone."""

    approved: bool
    notes: Optional[str] = None


class MilestoneResponse(MilestoneBase):
    """Schema for milestone response."""

    id: UUID
    project_id: UUID
    status: MilestoneStatus
    is_paid: bool
    completion_notes: Optional[str] = None
    completed_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MilestoneListResponse(BaseModel):
    """Schema for paginated milestone list response."""

    items: List[MilestoneResponse]
    total: int
    page: int
    page_size: int
    has_more: bool
