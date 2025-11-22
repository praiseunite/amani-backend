"""
Pydantic schemas for KYC operations.
"""

from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID

from app.models.kyc import KycType, KycStatus


class KycBase(BaseModel):
    """Base KYC schema with common fields."""

    type: KycType = Field(default=KycType.KYC, description="Type of KYC: kyc or kyb")
    nin_or_passport: str = Field(
        ..., min_length=5, max_length=100, description="National ID or Passport number"
    )


class KycCreate(KycBase):
    """Schema for KYC submission."""

    security_code: str = Field(..., min_length=4, description="Security code (will be hashed)")
    fingerprint: Optional[bytes] = Field(None, description="Fingerprint biometric data")
    image: Optional[bytes] = Field(None, description="Identity document image")


class KycResponse(KycBase):
    """Schema for KYC response."""

    id: UUID
    user_id: UUID
    status: KycStatus
    has_fingerprint: bool = Field(default=False, description="Whether fingerprint is stored")
    has_image: bool = Field(default=False, description="Whether document image is stored")
    has_approval_code: bool = Field(default=False, description="Whether approval code is set")
    rejection_reason: Optional[str] = None
    submitted_at: datetime
    verified_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_with_flags(cls, kyc_obj):
        """
        Create response from ORM object with computed flags.
        This avoids exposing binary data in responses.
        """
        data = {
            "id": kyc_obj.id,
            "user_id": kyc_obj.user_id,
            "type": kyc_obj.type,
            "nin_or_passport": kyc_obj.nin_or_passport,
            "status": kyc_obj.status,
            "has_fingerprint": kyc_obj.fingerprint is not None,
            "has_image": kyc_obj.image is not None,
            "has_approval_code": kyc_obj.approval_code is not None,
            "rejection_reason": kyc_obj.rejection_reason,
            "submitted_at": kyc_obj.submitted_at,
            "verified_at": kyc_obj.verified_at,
            "created_at": kyc_obj.created_at,
            "updated_at": kyc_obj.updated_at,
        }
        return cls(**data)


class KycUpdate(BaseModel):
    """Schema for updating KYC status (admin only)."""

    status: Optional[KycStatus] = None
    rejection_reason: Optional[str] = None
    approval_code: Optional[str] = Field(
        None, description="Approval code for clients (will be hashed)"
    )


class KycApproval(BaseModel):
    """Schema for KYC approval/rejection."""

    status: KycStatus = Field(..., description="New status: approved or rejected")
    rejection_reason: Optional[str] = Field(
        None, description="Reason for rejection (required if status is rejected)"
    )
    approval_code: Optional[str] = Field(
        None, description="Approval code for client (required if status is approved)"
    )
