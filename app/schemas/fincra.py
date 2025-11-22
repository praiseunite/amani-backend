"""
Pydantic schemas for FinCra payment operations.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from uuid import UUID
from decimal import Decimal


# Payment Schemas
class FinCraPaymentRequest(BaseModel):
    """Schema for FinCra payment creation request."""

    amount: Decimal = Field(..., gt=0, description="Payment amount")
    currency: str = Field(default="USD", pattern="^[A-Z]{3}$", description="Currency code")
    customer_email: EmailStr = Field(..., description="Customer email address")
    reference: str = Field(..., min_length=1, description="Unique payment reference")
    description: Optional[str] = Field(None, description="Payment description")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class FinCraPaymentResponse(BaseModel):
    """Schema for FinCra payment response."""

    id: str = Field(..., description="FinCra transaction ID")
    reference: str = Field(..., description="Payment reference")
    amount: Decimal = Field(..., description="Payment amount")
    currency: str = Field(..., description="Currency code")
    status: str = Field(..., description="Payment status")
    customer_email: str = Field(..., description="Customer email")
    description: Optional[str] = Field(None, description="Payment description")
    created_at: datetime = Field(..., description="Creation timestamp")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class FinCraPaymentVerifyRequest(BaseModel):
    """Schema for FinCra payment verification request."""

    transaction_id: str = Field(..., min_length=1, description="FinCra transaction ID")


class FinCraPaymentVerifyResponse(BaseModel):
    """Schema for FinCra payment verification response."""

    id: str = Field(..., description="FinCra transaction ID")
    reference: str = Field(..., description="Payment reference")
    amount: Decimal = Field(..., description="Payment amount")
    currency: str = Field(..., description="Currency code")
    status: str = Field(..., description="Payment status")
    verified: bool = Field(..., description="Verification status")
    verified_at: Optional[datetime] = Field(None, description="Verification timestamp")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


# Transfer Schemas
class FinCraTransferRequest(BaseModel):
    """Schema for FinCra transfer/payout creation request."""

    amount: Decimal = Field(..., gt=0, description="Transfer amount")
    currency: str = Field(default="USD", pattern="^[A-Z]{3}$", description="Currency code")
    recipient_account: str = Field(..., min_length=1, description="Recipient account number")
    recipient_bank_code: str = Field(..., min_length=1, description="Recipient bank code")
    reference: str = Field(..., min_length=1, description="Unique transfer reference")
    narration: Optional[str] = Field(None, description="Transfer narration")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class FinCraTransferResponse(BaseModel):
    """Schema for FinCra transfer response."""

    id: str = Field(..., description="FinCra transfer ID")
    reference: str = Field(..., description="Transfer reference")
    amount: Decimal = Field(..., description="Transfer amount")
    currency: str = Field(..., description="Currency code")
    status: str = Field(..., description="Transfer status")
    recipient_account: str = Field(..., description="Recipient account number")
    recipient_bank_code: str = Field(..., description="Recipient bank code")
    narration: Optional[str] = Field(None, description="Transfer narration")
    created_at: datetime = Field(..., description="Creation timestamp")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class FinCraTransferVerifyRequest(BaseModel):
    """Schema for FinCra transfer verification request."""

    transaction_id: str = Field(..., min_length=1, description="FinCra transfer ID")


class FinCraTransferVerifyResponse(BaseModel):
    """Schema for FinCra transfer verification response."""

    id: str = Field(..., description="FinCra transfer ID")
    reference: str = Field(..., description="Transfer reference")
    amount: Decimal = Field(..., description="Transfer amount")
    currency: str = Field(..., description="Currency code")
    status: str = Field(..., description="Transfer status")
    verified: bool = Field(..., description="Verification status")
    verified_at: Optional[datetime] = Field(None, description="Verification timestamp")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


# Balance Schemas
class FinCraBalanceRequest(BaseModel):
    """Schema for FinCra balance request."""

    currency: Optional[str] = Field(None, pattern="^[A-Z]{3}$", description="Optional currency filter")


class FinCraBalanceResponse(BaseModel):
    """Schema for FinCra balance response."""

    currency: str = Field(..., description="Currency code")
    available_balance: Decimal = Field(..., description="Available balance")
    ledger_balance: Decimal = Field(..., description="Ledger balance")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
