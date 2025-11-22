"""
Pydantic schemas for project operations.
"""

from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from uuid import UUID
from decimal import Decimal

from app.models.project import ProjectStatus


class ProjectBase(BaseModel):
    """Base project schema with common fields."""

    title: str = Field(..., min_length=3, max_length=255)
    description: str = Field(..., min_length=10)
    total_amount: Decimal = Field(..., gt=0)
    currency: str = Field(default="USD", pattern="^[A-Z]{3}$")
    completion_criteria: Optional[str] = None
    due_date: Optional[datetime] = None


class ProjectCreate(ProjectBase):
    """Schema for creating a new project."""

    buyer_id: Optional[UUID] = None
    seller_id: Optional[UUID] = None
    start_date: Optional[datetime] = None


class ProjectUpdate(BaseModel):
    """Schema for updating a project."""

    title: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = Field(None, min_length=10)
    total_amount: Optional[Decimal] = Field(None, gt=0)
    currency: Optional[str] = Field(None, pattern="^[A-Z]{3}$")
    completion_criteria: Optional[str] = None
    due_date: Optional[datetime] = None
    status: Optional[ProjectStatus] = None


class ProjectResponse(ProjectBase):
    """Schema for project response."""

    id: UUID
    status: ProjectStatus
    creator_id: UUID
    buyer_id: Optional[UUID] = None
    seller_id: Optional[UUID] = None
    terms_accepted_at: Optional[datetime] = None
    start_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectListResponse(BaseModel):
    """Schema for paginated project list response."""

    items: List[ProjectResponse]
    total: int
    page: int
    page_size: int
    has_more: bool
