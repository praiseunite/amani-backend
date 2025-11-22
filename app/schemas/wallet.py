"""
Pydantic schemas for wallet operations.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class WalletProvider(str, Enum):
    """Supported wallet providers."""

    FINCRA = "fincra"
    PAYSTACK = "paystack"
    FLUTTERWAVE = "flutterwave"


class WalletEventType(str, Enum):
    """Type of wallet transaction event."""

    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSFER_IN = "transfer_in"
    TRANSFER_OUT = "transfer_out"
    FEE = "fee"
    REFUND = "refund"
    HOLD = "hold"
    RELEASE = "release"


# Wallet Registry Schemas
class WalletRegistryBase(BaseModel):
    """Base wallet registry schema with common fields."""

    provider: WalletProvider
    provider_account_id: str = Field(..., min_length=1)
    provider_customer_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class WalletRegistryCreate(WalletRegistryBase):
    """Schema for creating a new wallet registry entry."""

    user_id: UUID


class WalletRegistryResponse(WalletRegistryBase):
    """Schema for wallet registry response."""

    id: UUID
    external_id: UUID
    user_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class WalletRegistryListResponse(BaseModel):
    """Schema for paginated wallet registry list response."""

    items: List[WalletRegistryResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


# Wallet Balance Snapshot Schemas
class WalletBalanceSnapshotBase(BaseModel):
    """Base wallet balance snapshot schema with common fields."""

    balance: Decimal = Field(..., ge=0)
    currency: str = Field(default="USD", pattern="^[A-Z]{3}$")


class WalletBalanceSnapshotCreate(WalletBalanceSnapshotBase):
    """Schema for creating a new wallet balance snapshot."""

    wallet_id: UUID
    provider: WalletProvider
    external_balance_id: Optional[str] = None
    as_of: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    idempotency_key: Optional[str] = None


class WalletBalanceSnapshotResponse(WalletBalanceSnapshotBase):
    """Schema for wallet balance snapshot response."""

    id: UUID
    wallet_id: UUID
    provider: WalletProvider
    external_balance_id: Optional[str] = None
    as_of: datetime
    metadata: Optional[Dict[str, Any]] = None
    idempotency_key: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class WalletBalanceSnapshotListResponse(BaseModel):
    """Schema for paginated wallet balance snapshot list response."""

    items: List[WalletBalanceSnapshotResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


# Wallet Transaction Event Schemas
class WalletTransactionEventBase(BaseModel):
    """Base wallet transaction event schema with common fields."""

    event_type: WalletEventType
    amount: Decimal = Field(..., gt=0)
    currency: str = Field(default="USD", pattern="^[A-Z]{3}$")
    occurred_at: datetime


class WalletTransactionEventCreate(WalletTransactionEventBase):
    """Schema for creating a new wallet transaction event."""

    wallet_id: UUID
    provider: WalletProvider
    provider_event_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    idempotency_key: Optional[str] = None


class WalletTransactionEventResponse(WalletTransactionEventBase):
    """Schema for wallet transaction event response."""

    id: UUID
    wallet_id: UUID
    provider: WalletProvider
    provider_event_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class WalletTransactionEventListResponse(BaseModel):
    """Schema for paginated wallet transaction event list response."""

    items: List[WalletTransactionEventResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


# Wallet Operations Schemas
class WalletSyncRequest(BaseModel):
    """Schema for wallet balance sync request."""

    wallet_id: UUID
    idempotency_key: Optional[str] = None


class WalletGetBalanceRequest(BaseModel):
    """Schema for get wallet balance request."""

    wallet_id: UUID
