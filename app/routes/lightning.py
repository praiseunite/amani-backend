"""
Lightning routes for LNbits Lightning Network operations.
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.core.lnbits import LNbitsError, get_lnbits_client
from app.models.user import User
from app.schemas.lnbits import (
    LNbitsBalanceResponse,
    LNbitsDecodeInvoiceRequest,
    LNbitsDecodeInvoiceResponse,
    LNbitsInternalTransferRequest,
    LNbitsInternalTransferResponse,
    LNbitsInvoiceCreateRequest,
    LNbitsInvoiceResponse,
    LNbitsPaymentRequest,
    LNbitsPaymentStatusRequest,
    LNbitsPaymentStatusResponse,
    LNbitsWalletCreateRequest,
    LNbitsWalletDetailsResponse,
    LNbitsWalletResponse,
)

router = APIRouter(prefix="/lightning", tags=["lightning"])
logger = logging.getLogger(__name__)


@router.post("/wallet/create", response_model=LNbitsWalletResponse, status_code=status.HTTP_201_CREATED)
async def create_lightning_wallet(
    wallet_data: LNbitsWalletCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new Lightning wallet via LNbits.

    Args:
        wallet_data: Wallet creation data
        current_user: Currently authenticated user
        db: Database session

    Returns:
        Wallet creation response from LNbits

    Raises:
        HTTPException: If wallet creation fails
    """
    try:
        lnbits_client = get_lnbits_client()

        # Create wallet with LNbits
        wallet_response = await lnbits_client.create_wallet(
            user_name=wallet_data.user_name or str(current_user.id),
            wallet_name=wallet_data.wallet_name,
        )

        logger.info(
            f"Lightning wallet created: {wallet_response.get('id')} for user {current_user.id}"
        )

        return LNbitsWalletResponse(
            id=wallet_response.get("id"),
            name=wallet_response.get("name"),
            user=wallet_response.get("user"),
            adminkey=wallet_response.get("adminkey"),
            inkey=wallet_response.get("inkey"),
            balance_msat=wallet_response.get("balance_msat", 0),
        )

    except LNbitsError as e:
        logger.error(f"LNbits wallet creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Wallet creation failed: {e.message}",
        )


@router.get("/wallet/details", response_model=LNbitsWalletDetailsResponse)
async def get_wallet_details(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get Lightning wallet details and balance.

    Args:
        current_user: Currently authenticated user
        db: Database session

    Returns:
        Wallet details from LNbits

    Raises:
        HTTPException: If retrieval fails
    """
    try:
        lnbits_client = get_lnbits_client()

        # Get wallet details
        wallet_details = await lnbits_client.get_wallet_details()

        logger.info(f"Lightning wallet details retrieved for user {current_user.id}")

        return LNbitsWalletDetailsResponse(
            id=wallet_details.get("id"),
            name=wallet_details.get("name"),
            balance=wallet_details.get("balance", 0),
        )

    except LNbitsError as e:
        logger.error(f"LNbits wallet details retrieval failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Wallet details retrieval failed: {e.message}",
        )


@router.post("/invoice/create", response_model=LNbitsInvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    invoice_data: LNbitsInvoiceCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a Lightning invoice (payment request).

    Args:
        invoice_data: Invoice creation data
        current_user: Currently authenticated user
        db: Database session

    Returns:
        Invoice response with payment_request (BOLT11)

    Raises:
        HTTPException: If invoice creation fails
    """
    try:
        lnbits_client = get_lnbits_client()

        # Create invoice with LNbits
        invoice_response = await lnbits_client.create_invoice(
            amount=invoice_data.amount,
            memo=invoice_data.memo,
            unit=invoice_data.unit,
            expiry=invoice_data.expiry,
            webhook=invoice_data.webhook,
        )

        logger.info(
            f"Lightning invoice created: {invoice_response.get('payment_hash')} for user {current_user.id} "
            f"- {invoice_data.amount} {invoice_data.unit}"
        )

        return LNbitsInvoiceResponse(
            payment_hash=invoice_response.get("payment_hash"),
            payment_request=invoice_response.get("payment_request"),
            checking_id=invoice_response.get("checking_id"),
            lnurl_response=invoice_response.get("lnurl_response"),
        )

    except LNbitsError as e:
        logger.error(f"LNbits invoice creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Invoice creation failed: {e.message}",
        )


@router.post("/invoice/check", response_model=LNbitsPaymentStatusResponse)
async def check_invoice_status(
    status_data: LNbitsPaymentStatusRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Check Lightning invoice/payment status.

    Args:
        status_data: Payment status request data
        current_user: Currently authenticated user
        db: Database session

    Returns:
        Payment status response

    Raises:
        HTTPException: If status check fails
    """
    try:
        lnbits_client = get_lnbits_client()

        # Check invoice status
        status_response = await lnbits_client.check_invoice(status_data.payment_hash)

        logger.info(f"Lightning invoice status checked: {status_data.payment_hash} for user {current_user.id}")

        return LNbitsPaymentStatusResponse(
            checking_id=status_response.get("checking_id"),
            pending=status_response.get("pending"),
            amount=status_response.get("amount"),
            fee=status_response.get("fee"),
            memo=status_response.get("memo"),
            time=status_response.get("time"),
            bolt11=status_response.get("bolt11"),
            preimage=status_response.get("preimage"),
            payment_hash=status_response.get("payment_hash"),
            expiry=status_response.get("expiry"),
            extra=status_response.get("extra"),
            wallet_id=status_response.get("wallet_id"),
            webhook=status_response.get("webhook"),
            webhook_status=status_response.get("webhook_status"),
        )

    except LNbitsError as e:
        logger.error(f"LNbits invoice status check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Invoice status check failed: {e.message}",
        )


@router.post("/invoice/decode", response_model=LNbitsDecodeInvoiceResponse)
async def decode_invoice(
    decode_data: LNbitsDecodeInvoiceRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Decode a Lightning invoice (BOLT11).

    Args:
        decode_data: Invoice decode request data
        current_user: Currently authenticated user
        db: Database session

    Returns:
        Decoded invoice data

    Raises:
        HTTPException: If decoding fails
    """
    try:
        lnbits_client = get_lnbits_client()

        # Decode invoice
        decode_response = await lnbits_client.decode_invoice(decode_data.payment_request)

        logger.info(f"Lightning invoice decoded for user {current_user.id}")

        return LNbitsDecodeInvoiceResponse(
            payment_hash=decode_response.get("payment_hash"),
            amount_msat=decode_response.get("amount_msat"),
            description=decode_response.get("description"),
            description_hash=decode_response.get("description_hash"),
            payee=decode_response.get("payee"),
            date=decode_response.get("date"),
            expiry=decode_response.get("expiry"),
            min_final_cltv_expiry=decode_response.get("min_final_cltv_expiry"),
        )

    except LNbitsError as e:
        logger.error(f"LNbits invoice decode failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Invoice decode failed: {e.message}",
        )


@router.post("/payment/send", response_model=LNbitsPaymentStatusResponse)
async def pay_invoice(
    payment_data: LNbitsPaymentRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Pay a Lightning invoice.

    Args:
        payment_data: Payment request data
        current_user: Currently authenticated user
        db: Database session

    Returns:
        Payment result

    Raises:
        HTTPException: If payment fails
    """
    try:
        lnbits_client = get_lnbits_client()

        # Pay invoice
        payment_response = await lnbits_client.pay_invoice(
            bolt11=payment_data.bolt11,
            out=payment_data.out,
        )

        logger.info(f"Lightning payment sent for user {current_user.id}")

        return LNbitsPaymentStatusResponse(
            checking_id=payment_response.get("checking_id"),
            pending=payment_response.get("pending", False),
            amount=payment_response.get("amount"),
            fee=payment_response.get("fee"),
            memo=payment_response.get("memo"),
            time=payment_response.get("time"),
            bolt11=payment_response.get("bolt11"),
            preimage=payment_response.get("preimage"),
            payment_hash=payment_response.get("payment_hash"),
            expiry=payment_response.get("expiry"),
            extra=payment_response.get("extra"),
            wallet_id=payment_response.get("wallet_id"),
            webhook=payment_response.get("webhook"),
            webhook_status=payment_response.get("webhook_status"),
        )

    except LNbitsError as e:
        logger.error(f"LNbits payment failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Payment failed: {e.message}",
        )


@router.get("/balance", response_model=LNbitsBalanceResponse)
async def get_balance(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get Lightning wallet balance.

    Args:
        current_user: Currently authenticated user
        db: Database session

    Returns:
        Balance response

    Raises:
        HTTPException: If balance retrieval fails
    """
    try:
        lnbits_client = get_lnbits_client()

        # Get balance
        balance_response = await lnbits_client.get_balance()

        logger.info(f"Lightning balance retrieved for user {current_user.id}")

        return LNbitsBalanceResponse(
            balance=balance_response.get("balance"),
            currency=balance_response.get("currency", "msat"),
        )

    except LNbitsError as e:
        logger.error(f"LNbits balance retrieval failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Balance retrieval failed: {e.message}",
        )
