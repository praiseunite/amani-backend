"""
Pydantic schemas for LNbits Lightning operations.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# Wallet Schemas
class LNbitsWalletCreateRequest(BaseModel):
    """Schema for LNbits wallet creation request."""

    user_name: str = Field(..., min_length=1, description="User identifier")
    wallet_name: Optional[str] = Field(None, description="Optional wallet name")


class LNbitsWalletResponse(BaseModel):
    """Schema for LNbits wallet response."""

    id: str = Field(..., description="Wallet ID")
    name: str = Field(..., description="Wallet name")
    user: str = Field(..., description="User identifier")
    adminkey: Optional[str] = Field(None, description="Admin key for wallet operations")
    inkey: Optional[str] = Field(None, description="Invoice key (read-only)")
    balance_msat: Optional[int] = Field(None, description="Wallet balance in millisatoshis")


class LNbitsWalletDetailsResponse(BaseModel):
    """Schema for LNbits wallet details."""

    id: str = Field(..., description="Wallet ID")
    name: str = Field(..., description="Wallet name")
    balance: int = Field(..., description="Balance in millisatoshis")


# Invoice Schemas
class LNbitsInvoiceCreateRequest(BaseModel):
    """Schema for creating a Lightning invoice."""

    amount: int = Field(..., gt=0, description="Amount in satoshis")
    memo: Optional[str] = Field(None, max_length=639, description="Invoice memo/description")
    unit: str = Field(default="sat", description="Unit: 'sat' or 'msat'")
    expiry: Optional[int] = Field(None, gt=0, description="Expiry time in seconds")
    webhook: Optional[str] = Field(None, description="Webhook URL for payment notifications")


class LNbitsInvoiceResponse(BaseModel):
    """Schema for Lightning invoice response."""

    payment_hash: str = Field(..., description="Payment hash")
    payment_request: str = Field(..., description="BOLT11 payment request")
    checking_id: str = Field(..., description="Internal checking ID")
    lnurl_response: Optional[str] = Field(None, description="LNURL response")


# Payment Schemas
class LNbitsPaymentRequest(BaseModel):
    """Schema for making a Lightning payment."""

    bolt11: str = Field(..., description="BOLT11 payment request to pay")
    out: bool = Field(default=True, description="Must be True for outgoing payments")


class LNbitsPaymentStatusRequest(BaseModel):
    """Schema for checking payment status."""

    payment_hash: str = Field(..., min_length=1, description="Payment hash to check")


class LNbitsPaymentStatusResponse(BaseModel):
    """Schema for payment status response."""

    checking_id: str = Field(..., description="Internal checking ID")
    pending: bool = Field(..., description="Whether payment is pending")
    amount: int = Field(..., description="Amount in millisatoshis")
    fee: Optional[int] = Field(None, description="Fee in millisatoshis")
    memo: Optional[str] = Field(None, description="Payment memo")
    time: int = Field(..., description="Timestamp")
    bolt11: Optional[str] = Field(None, description="BOLT11 payment request")
    preimage: Optional[str] = Field(None, description="Payment preimage (proof of payment)")
    payment_hash: str = Field(..., description="Payment hash")
    expiry: Optional[int] = Field(None, description="Expiry timestamp")
    extra: Optional[Dict[str, Any]] = Field(None, description="Extra metadata")
    wallet_id: str = Field(..., description="Wallet ID")
    webhook: Optional[str] = Field(None, description="Webhook URL")
    webhook_status: Optional[int] = Field(None, description="Webhook delivery status")


# Invoice Decode Schemas
class LNbitsDecodeInvoiceRequest(BaseModel):
    """Schema for decoding a Lightning invoice."""

    payment_request: str = Field(..., description="BOLT11 payment request to decode")


class LNbitsDecodeInvoiceResponse(BaseModel):
    """Schema for decoded invoice response."""

    payment_hash: str = Field(..., description="Payment hash")
    amount_msat: int = Field(..., description="Amount in millisatoshis")
    description: Optional[str] = Field(None, description="Invoice description")
    description_hash: Optional[str] = Field(None, description="Description hash")
    payee: Optional[str] = Field(None, description="Payee node public key")
    date: int = Field(..., description="Creation timestamp")
    expiry: int = Field(..., description="Expiry seconds")
    min_final_cltv_expiry: Optional[int] = Field(None, description="Minimum CLTV expiry")


# Balance Schemas
class LNbitsBalanceResponse(BaseModel):
    """Schema for wallet balance response."""

    balance: int = Field(..., description="Balance in millisatoshis")
    currency: str = Field(default="msat", description="Currency unit")


# Transfer Schemas
class LNbitsInternalTransferRequest(BaseModel):
    """Schema for internal transfer between LNbits wallets."""

    destination_wallet_id: str = Field(..., description="Destination wallet ID")
    amount: int = Field(..., gt=0, description="Amount in satoshis")
    memo: Optional[str] = Field(None, description="Transfer memo")


class LNbitsInternalTransferResponse(BaseModel):
    """Schema for internal transfer response."""

    payment_hash: str = Field(..., description="Payment hash")
    checking_id: str = Field(..., description="Checking ID")
    amount: int = Field(..., description="Amount transferred")
    fee: int = Field(default=0, description="Fee (usually 0 for internal transfers)")
