"""
Pydantic schemas for transaction operations.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from decimal import Decimal

from app.models.transaction import TransactionType, TransactionStatus


class TransactionBase(BaseModel):
    """Base transaction schema with common fields."""
    amount: Decimal = Field(..., gt=0)
    currency: str = Field(default="USD", pattern="^[A-Z]{3}$")
    description: Optional[str] = None


class TransactionCreate(TransactionBase):
    """Schema for creating a new transaction."""
    transaction_type: TransactionType
    project_id: Optional[UUID] = None


class EscrowHoldRequest(BaseModel):
    """Schema for holding funds in escrow."""
    project_id: UUID
    amount: Decimal = Field(..., gt=0)
    currency: str = Field(default="USD", pattern="^[A-Z]{3}$")
    payment_method: str = Field(..., description="Payment method for FinCra")
    payment_details: Optional[Dict[str, Any]] = None


class EscrowReleaseRequest(BaseModel):
    """Schema for releasing escrow funds."""
    milestone_id: UUID
    notes: Optional[str] = None


class TransactionResponse(TransactionBase):
    """Schema for transaction response."""
    id: UUID
    user_id: UUID
    project_id: Optional[UUID] = None
    transaction_type: TransactionType
    status: TransactionStatus
    fee: Decimal
    net_amount: Decimal
    payment_gateway: Optional[str] = None
    gateway_transaction_id: Optional[str] = None
    gateway_reference: Optional[str] = None
    gateway_response: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    processed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    model_config = {
        "from_attributes": True
    }


class TransactionListResponse(BaseModel):
    """Schema for paginated transaction list response."""
    items: List[TransactionResponse]
    total: int
    page: int
    page_size: int
    has_more: bool
