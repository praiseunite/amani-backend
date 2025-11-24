"""
Bot-specific routes for Lightning wallet operations.
These endpoints are designed for the bitbot integration.
"""

import logging
import secrets
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.core.lnbits import LNbitsError, get_lnbits_client
from app.models.user import User

router = APIRouter(prefix="/bot", tags=["bot"])
logger = logging.getLogger(__name__)


# Schemas for bot operations
class MagicLinkCreateRequest(BaseModel):
    """Request to create a magic link (cheque/claim)."""

    amount: int = Field(..., gt=0, description="Amount in satoshis")
    memo: Optional[str] = Field(None, description="Memo for the cheque")
    expiry_hours: int = Field(default=24, ge=1, le=168, description="Expiry time in hours (1-168)")


class MagicLinkResponse(BaseModel):
    """Response with magic link details."""

    link_id: str = Field(..., description="Unique link identifier")
    magic_link: str = Field(..., description="Magic link URL for claiming")
    amount: int = Field(..., description="Amount in satoshis")
    memo: Optional[str] = Field(None, description="Memo")
    expires_at: datetime = Field(..., description="Link expiry time")
    created_at: datetime = Field(..., description="Creation time")


class MagicLinkClaimRequest(BaseModel):
    """Request to claim a magic link."""

    link_id: str = Field(..., description="Magic link identifier")


class MagicLinkClaimResponse(BaseModel):
    """Response after claiming a magic link."""

    success: bool = Field(..., description="Whether claim was successful")
    amount: int = Field(..., description="Amount claimed in satoshis")
    payment_hash: str = Field(..., description="Payment hash")


class FaucetClaimRequest(BaseModel):
    """Request to claim from faucet."""

    pass  # No parameters needed, uses authenticated user


class FaucetClaimResponse(BaseModel):
    """Response from faucet claim."""

    success: bool = Field(..., description="Whether claim was successful")
    amount: int = Field(..., description="Amount claimed in satoshis")
    next_claim_at: Optional[datetime] = Field(None, description="When user can claim again")


class InternalTransferRequest(BaseModel):
    """Request for internal transfer between users."""

    recipient_user_id: UUID = Field(..., description="Recipient user ID")
    amount: int = Field(..., gt=0, description="Amount in satoshis")
    memo: Optional[str] = Field(None, description="Transfer memo")
    pin: Optional[str] = Field(None, description="Security PIN if withdrawal protection enabled")


class InternalTransferResponse(BaseModel):
    """Response from internal transfer."""

    success: bool = Field(..., description="Whether transfer was successful")
    amount: int = Field(..., description="Amount transferred in satoshis")
    fee: int = Field(default=0, description="Transfer fee")
    payment_hash: str = Field(..., description="Payment hash")


class WithdrawalPINSetRequest(BaseModel):
    """Request to set withdrawal PIN."""

    pin: str = Field(..., min_length=4, max_length=6, description="4-6 digit PIN")


class WithdrawalPINVerifyRequest(BaseModel):
    """Request to verify withdrawal PIN."""

    pin: str = Field(..., description="PIN to verify")


class WithdrawalPINResponse(BaseModel):
    """Response for PIN operations."""

    success: bool = Field(..., description="Whether operation was successful")
    message: str = Field(..., description="Response message")


# In-memory storage for demo purposes
# PRODUCTION NOTE: These should be replaced with database persistence for:
# - Data durability across restarts
# - Horizontal scaling across multiple instances
# - Better security (encrypted PIN storage with bcrypt)
# - Query capabilities and audit trails
# See LNBITS_MIGRATION.md for database schema examples
magic_links_storage = {}
faucet_claims_storage = {}
user_pins_storage = {}


@router.post("/magic-link/create", response_model=MagicLinkResponse, status_code=status.HTTP_201_CREATED)
async def create_magic_link(
    request: MagicLinkCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a magic link (cheque) for claiming sats.
    
    This creates a claimable Lightning payment that can be shared via link.
    Similar to a Bitcoin cheque that anyone with the link can claim.

    Args:
        request: Magic link creation request
        current_user: Currently authenticated user
        db: Database session

    Returns:
        Magic link response with claim URL

    Raises:
        HTTPException: If creation fails
    """
    try:
        lnbits_client = get_lnbits_client()

        # Generate unique link ID
        link_id = secrets.token_urlsafe(16)
        
        # Create invoice for the amount
        invoice_response = await lnbits_client.create_invoice(
            amount=request.amount,
            memo=request.memo or f"Magic link by {current_user.email}",
            unit="sat",
            expiry=request.expiry_hours * 3600,
        )

        # Store magic link details
        expires_at = datetime.utcnow() + timedelta(hours=request.expiry_hours)
        magic_links_storage[link_id] = {
            "user_id": str(current_user.id),
            "amount": request.amount,
            "memo": request.memo,
            "payment_hash": invoice_response.get("payment_hash"),
            "payment_request": invoice_response.get("payment_request"),
            "expires_at": expires_at,
            "created_at": datetime.utcnow(),
            "claimed": False,
        }

        # Generate magic link URL
        magic_link = f"/api/v1/bot/magic-link/claim/{link_id}"

        logger.info(f"Magic link created: {link_id} by user {current_user.id} for {request.amount} sats")

        return MagicLinkResponse(
            link_id=link_id,
            magic_link=magic_link,
            amount=request.amount,
            memo=request.memo,
            expires_at=expires_at,
            created_at=datetime.utcnow(),
        )

    except LNbitsError as e:
        logger.error(f"Magic link creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Magic link creation failed: {e.message}",
        )


@router.post("/magic-link/claim/{link_id}", response_model=MagicLinkClaimResponse)
async def claim_magic_link(
    link_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Claim a magic link (cheque).
    
    Transfers the sats from the magic link to the claiming user's wallet.

    Args:
        link_id: Magic link identifier
        current_user: Currently authenticated user
        db: Database session

    Returns:
        Claim response with payment details

    Raises:
        HTTPException: If claim fails or link is invalid
    """
    # Check if link exists
    if link_id not in magic_links_storage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Magic link not found or already claimed",
        )

    link_data = magic_links_storage[link_id]

    # Check if already claimed
    if link_data["claimed"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Magic link already claimed",
        )

    # Check if expired
    if datetime.utcnow() > link_data["expires_at"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Magic link has expired",
        )

    # Cannot claim your own link
    if str(current_user.id) == link_data["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot claim your own magic link",
        )

    try:
        lnbits_client = get_lnbits_client()

        # Create invoice for recipient
        recipient_invoice = await lnbits_client.create_invoice(
            amount=link_data["amount"],
            memo=f"Claimed magic link: {link_data['memo'] or 'No memo'}",
            unit="sat",
        )

        # Pay the invoice (simulate transfer)
        # In production, this would actually transfer funds
        payment_hash = recipient_invoice.get("payment_hash")

        # Mark as claimed
        link_data["claimed"] = True
        link_data["claimed_by"] = str(current_user.id)
        link_data["claimed_at"] = datetime.utcnow()

        logger.info(f"Magic link claimed: {link_id} by user {current_user.id}")

        return MagicLinkClaimResponse(
            success=True,
            amount=link_data["amount"],
            payment_hash=payment_hash,
        )

    except LNbitsError as e:
        logger.error(f"Magic link claim failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Magic link claim failed: {e.message}",
        )


@router.post("/faucet/claim", response_model=FaucetClaimResponse)
async def claim_faucet(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Claim sats from the faucet (play balance).
    
    Users can claim a small amount of sats periodically for testing/playing.
    Rate limited to once per 24 hours per user.

    Args:
        current_user: Currently authenticated user
        db: Database session

    Returns:
        Faucet claim response

    Raises:
        HTTPException: If claim fails or user claimed too recently
    """
    user_id = str(current_user.id)
    faucet_amount = 100  # 100 sats per claim
    cooldown_hours = 24

    # Check last claim time
    if user_id in faucet_claims_storage:
        last_claim = faucet_claims_storage[user_id]
        next_claim_at = last_claim + timedelta(hours=cooldown_hours)
        if datetime.utcnow() < next_claim_at:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Faucet claimed too recently. Try again at {next_claim_at.isoformat()}",
            )

    try:
        lnbits_client = get_lnbits_client()

        # Create invoice for faucet claim
        invoice_response = await lnbits_client.create_invoice(
            amount=faucet_amount,
            memo="Faucet claim",
            unit="sat",
        )

        # Update last claim time
        faucet_claims_storage[user_id] = datetime.utcnow()
        next_claim_at = datetime.utcnow() + timedelta(hours=cooldown_hours)

        logger.info(f"Faucet claimed: {faucet_amount} sats by user {current_user.id}")

        return FaucetClaimResponse(
            success=True,
            amount=faucet_amount,
            next_claim_at=next_claim_at,
        )

    except LNbitsError as e:
        logger.error(f"Faucet claim failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Faucet claim failed: {e.message}",
        )


@router.post("/transfer/internal", response_model=InternalTransferResponse)
async def internal_transfer(
    request: InternalTransferRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Transfer sats internally between platform users.
    
    No Lightning invoice needed - instant transfer between wallets.
    Optionally requires PIN for withdrawal protection.

    Args:
        request: Internal transfer request
        current_user: Currently authenticated user
        db: Database session

    Returns:
        Transfer response

    Raises:
        HTTPException: If transfer fails or PIN is incorrect
    """
    # Cannot transfer to self
    if request.recipient_user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot transfer to yourself",
        )

    # Check if PIN is required and verify
    user_id = str(current_user.id)
    if user_id in user_pins_storage:
        if not request.pin:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="PIN required for withdrawal",
            )
        if user_pins_storage[user_id] != request.pin:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect PIN",
            )

    try:
        lnbits_client = get_lnbits_client()

        # Create invoice for recipient (simulating internal transfer)
        invoice_response = await lnbits_client.create_invoice(
            amount=request.amount,
            memo=request.memo or f"Internal transfer from {current_user.email}",
            unit="sat",
        )

        payment_hash = invoice_response.get("payment_hash")

        logger.info(
            f"Internal transfer: {request.amount} sats from {current_user.id} to {request.recipient_user_id}"
        )

        return InternalTransferResponse(
            success=True,
            amount=request.amount,
            fee=0,  # No fee for internal transfers
            payment_hash=payment_hash,
        )

    except LNbitsError as e:
        logger.error(f"Internal transfer failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Internal transfer failed: {e.message}",
        )


@router.post("/withdrawal/pin/set", response_model=WithdrawalPINResponse)
async def set_withdrawal_pin(
    request: WithdrawalPINSetRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Set a security PIN for withdrawal protection.
    
    Once set, the PIN will be required for all withdrawals and transfers.

    Args:
        request: PIN set request
        current_user: Currently authenticated user
        db: Database session

    Returns:
        PIN operation response
    """
    # Validate PIN format (digits only)
    if not request.pin.isdigit():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PIN must contain only digits",
        )

    # Check for common weak PINs (basic security)
    weak_pins = ["0000", "1111", "2222", "3333", "4444", "5555", "6666", "7777", "8888", "9999", "1234", "4321"]
    if request.pin in weak_pins:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PIN is too weak. Please choose a stronger PIN.",
        )

    user_id = str(current_user.id)
    user_pins_storage[user_id] = request.pin

    logger.info(f"Withdrawal PIN set for user {current_user.id}")

    return WithdrawalPINResponse(
        success=True,
        message="Withdrawal PIN set successfully",
    )


@router.post("/withdrawal/pin/verify", response_model=WithdrawalPINResponse)
async def verify_withdrawal_pin(
    request: WithdrawalPINVerifyRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Verify withdrawal PIN.
    
    SECURITY NOTE: In production, implement:
    - Rate limiting (e.g., 5 attempts per hour)
    - Account lockout after failed attempts
    - Logging of all verification attempts
    - Consider using timing-safe comparison

    Args:
        request: PIN verify request
        current_user: Currently authenticated user
        db: Database session

    Returns:
        PIN verification response
    """
    user_id = str(current_user.id)

    if user_id not in user_pins_storage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No PIN set for this user",
        )

    # PRODUCTION: Implement rate limiting here to prevent brute force
    # Example: Check failed_attempts table and reject if > 5 in last hour
    
    if user_pins_storage[user_id] != request.pin:
        # PRODUCTION: Log failed attempt with timestamp
        return WithdrawalPINResponse(
            success=False,
            message="Incorrect PIN",
        )

    return WithdrawalPINResponse(
        success=True,
        message="PIN verified successfully",
    )


@router.delete("/withdrawal/pin", response_model=WithdrawalPINResponse)
async def remove_withdrawal_pin(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Remove withdrawal PIN protection.

    Args:
        current_user: Currently authenticated user
        db: Database session

    Returns:
        PIN operation response
    """
    user_id = str(current_user.id)

    if user_id in user_pins_storage:
        del user_pins_storage[user_id]

    logger.info(f"Withdrawal PIN removed for user {current_user.id}")

    return WithdrawalPINResponse(
        success=True,
        message="Withdrawal PIN removed successfully",
    )
