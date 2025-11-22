"""
Payment routes for FinCra payment operations.
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.core.fincra import FinCraError, get_fincra_client
from app.models.user import User
from app.schemas.fincra import (
    FinCraBalanceRequest,
    FinCraBalanceResponse,
    FinCraPaymentRequest,
    FinCraPaymentResponse,
    FinCraPaymentVerifyRequest,
    FinCraPaymentVerifyResponse,
    FinCraTransferRequest,
    FinCraTransferResponse,
    FinCraTransferVerifyRequest,
    FinCraTransferVerifyResponse,
)

router = APIRouter(prefix="/payment", tags=["payment"])
logger = logging.getLogger(__name__)


@router.post("/create", response_model=FinCraPaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
    payment_data: FinCraPaymentRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a payment transaction via FinCra.

    Args:
        payment_data: Payment creation data
        current_user: Currently authenticated user
        db: Database session

    Returns:
        Payment response from FinCra

    Raises:
        HTTPException: If payment creation fails
    """
    try:
        fincra_client = get_fincra_client()

        # Create payment with FinCra
        payment_response = await fincra_client.create_payment(
            amount=payment_data.amount,
            currency=payment_data.currency,
            customer_email=payment_data.customer_email,
            reference=payment_data.reference,
            description=payment_data.description,
            metadata=payment_data.metadata or {},
        )

        # Extract payment data from response
        payment_result = payment_response.get("data", {})

        logger.info(
            f"Payment created: {payment_result.get('id')} for user {current_user.id} "
            f"- {payment_data.amount} {payment_data.currency}"
        )

        return FinCraPaymentResponse(
            id=payment_result.get("id"),
            reference=payment_result.get("reference"),
            amount=payment_result.get("amount"),
            currency=payment_result.get("currency"),
            status=payment_result.get("status"),
            customer_email=payment_result.get("customer", {}).get("email"),
            description=payment_result.get("description"),
            created_at=payment_result.get("created_at"),
            metadata=payment_result.get("metadata"),
        )

    except FinCraError as e:
        logger.error(f"FinCra payment creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Payment creation failed: {e.message}",
        )


@router.post("/verify", response_model=FinCraPaymentVerifyResponse)
async def verify_payment(
    verify_data: FinCraPaymentVerifyRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Verify a payment transaction with FinCra.

    Args:
        verify_data: Payment verification data
        current_user: Currently authenticated user
        db: Database session

    Returns:
        Payment verification response from FinCra

    Raises:
        HTTPException: If verification fails
    """
    try:
        fincra_client = get_fincra_client()

        # Verify payment with FinCra
        verification_response = await fincra_client.verify_payment(verify_data.transaction_id)

        # Extract verification data from response
        verification_result = verification_response.get("data", {})

        logger.info(f"Payment verified: {verify_data.transaction_id} for user {current_user.id}")

        return FinCraPaymentVerifyResponse(
            id=verification_result.get("id"),
            reference=verification_result.get("reference"),
            amount=verification_result.get("amount"),
            currency=verification_result.get("currency"),
            status=verification_result.get("status"),
            verified=verification_result.get("status") in ["success", "completed"],
            verified_at=verification_result.get("verified_at"),
            metadata=verification_result.get("metadata"),
        )

    except FinCraError as e:
        logger.error(f"FinCra payment verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Payment verification failed: {e.message}",
        )


@router.post(
    "/transfer/create", response_model=FinCraTransferResponse, status_code=status.HTTP_201_CREATED
)
async def create_transfer(
    transfer_data: FinCraTransferRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a transfer/payout transaction via FinCra.

    Args:
        transfer_data: Transfer creation data
        current_user: Currently authenticated user
        db: Database session

    Returns:
        Transfer response from FinCra

    Raises:
        HTTPException: If transfer creation fails
    """
    try:
        fincra_client = get_fincra_client()

        # Create transfer with FinCra
        transfer_response = await fincra_client.create_transfer(
            amount=transfer_data.amount,
            currency=transfer_data.currency,
            recipient_account=transfer_data.recipient_account,
            recipient_bank_code=transfer_data.recipient_bank_code,
            reference=transfer_data.reference,
            narration=transfer_data.narration,
            metadata=transfer_data.metadata or {},
        )

        # Extract transfer data from response
        transfer_result = transfer_response.get("data", {})

        logger.info(
            f"Transfer created: {transfer_result.get('id')} for user {current_user.id} "
            f"- {transfer_data.amount} {transfer_data.currency}"
        )

        return FinCraTransferResponse(
            id=transfer_result.get("id"),
            reference=transfer_result.get("reference"),
            amount=transfer_result.get("amount"),
            currency=transfer_result.get("currency"),
            status=transfer_result.get("status"),
            recipient_account=transfer_result.get("beneficiary", {}).get("accountNumber"),
            recipient_bank_code=transfer_result.get("beneficiary", {}).get("bankCode"),
            narration=transfer_result.get("narration"),
            created_at=transfer_result.get("created_at"),
            metadata=transfer_result.get("metadata"),
        )

    except FinCraError as e:
        logger.error(f"FinCra transfer creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Transfer creation failed: {e.message}",
        )


@router.post("/transfer/verify", response_model=FinCraTransferVerifyResponse)
async def verify_transfer(
    verify_data: FinCraTransferVerifyRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Verify a transfer transaction with FinCra.

    Args:
        verify_data: Transfer verification data
        current_user: Currently authenticated user
        db: Database session

    Returns:
        Transfer verification response from FinCra

    Raises:
        HTTPException: If verification fails
    """
    try:
        fincra_client = get_fincra_client()

        # Verify transfer with FinCra
        verification_response = await fincra_client.verify_transfer(verify_data.transaction_id)

        # Extract verification data from response
        verification_result = verification_response.get("data", {})

        logger.info(f"Transfer verified: {verify_data.transaction_id} for user {current_user.id}")

        return FinCraTransferVerifyResponse(
            id=verification_result.get("id"),
            reference=verification_result.get("reference"),
            amount=verification_result.get("amount"),
            currency=verification_result.get("currency"),
            status=verification_result.get("status"),
            verified=verification_result.get("status") in ["success", "completed"],
            verified_at=verification_result.get("verified_at"),
            metadata=verification_result.get("metadata"),
        )

    except FinCraError as e:
        logger.error(f"FinCra transfer verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Transfer verification failed: {e.message}",
        )


@router.post("/balance", response_model=FinCraBalanceResponse)
async def get_balance(
    balance_data: FinCraBalanceRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get account balance from FinCra.

    Args:
        balance_data: Balance request data
        current_user: Currently authenticated user
        db: Database session

    Returns:
        Balance response from FinCra

    Raises:
        HTTPException: If balance retrieval fails
    """
    # Only allow superusers to check balance
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can check account balance",
        )

    try:
        fincra_client = get_fincra_client()

        # Get balance from FinCra
        balance_response = await fincra_client.get_balance(currency=balance_data.currency)

        # Extract balance data from response
        balance_result = balance_response.get("data", {})

        logger.info(f"Balance retrieved for user {current_user.id}")

        return FinCraBalanceResponse(
            currency=balance_result.get("currency"),
            available_balance=balance_result.get("available_balance"),
            ledger_balance=balance_result.get("ledger_balance"),
            metadata=balance_result.get("metadata"),
        )

    except FinCraError as e:
        logger.error(f"FinCra balance retrieval failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Balance retrieval failed: {e.message}",
        )
