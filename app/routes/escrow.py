"""
Escrow and transaction routes for payment processing.
Integrates with FinCra API for payments.
"""

import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.core.fincra import FinCraError, get_fincra_client
from app.models.milestone import Milestone, MilestoneStatus
from app.models.project import Project, ProjectStatus
from app.models.transaction import Transaction, TransactionStatus, TransactionType
from app.models.user import User
from app.schemas.transaction import (
    EscrowHoldRequest,
    EscrowReleaseRequest,
    TransactionListResponse,
    TransactionResponse,
)

router = APIRouter(prefix="/escrow", tags=["escrow"])
logger = logging.getLogger(__name__)


@router.post("/hold", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def hold_escrow_funds(
    escrow_data: EscrowHoldRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Hold funds in escrow for a project.
    This creates a payment transaction via FinCra and holds the funds.

    Args:
        escrow_data: Escrow hold request data
        current_user: Currently authenticated user
        db: Database session

    Returns:
        Created transaction

    Raises:
        HTTPException: If project not found, user not authorized, or payment fails
    """
    # Fetch project
    result = await db.execute(select(Project).where(Project.id == escrow_data.project_id))
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    # Only buyer can hold funds in escrow
    if project.buyer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Only the buyer can hold funds in escrow"
        )

    # Calculate fees (example: 2.5% platform fee)
    fee = escrow_data.amount * 0.025
    net_amount = escrow_data.amount - fee

    # Create transaction record
    transaction = Transaction(
        user_id=current_user.id,
        project_id=project.id,
        transaction_type=TransactionType.ESCROW_HOLD,
        status=TransactionStatus.PENDING,
        amount=escrow_data.amount,
        currency=escrow_data.currency,
        fee=fee,
        net_amount=net_amount,
        payment_gateway="fincra",
        description=f"Escrow hold for project: {project.title}",
    )

    db.add(transaction)
    await db.commit()
    await db.refresh(transaction)

    # Process payment via FinCra
    try:
        fincra_client = get_fincra_client()

        # Create payment with FinCra
        payment_response = await fincra_client.create_payment(
            amount=escrow_data.amount,
            currency=escrow_data.currency,
            customer_email=current_user.email,
            reference=str(transaction.id),
            description=transaction.description,
            metadata={
                "project_id": str(project.id),
                "transaction_type": "escrow_hold",
                "payment_method": escrow_data.payment_method,
            },
        )

        # Update transaction with FinCra response
        transaction.status = TransactionStatus.PROCESSING
        transaction.gateway_transaction_id = payment_response.get("data", {}).get("id")
        transaction.gateway_reference = payment_response.get("data", {}).get("reference")
        transaction.gateway_response = payment_response
        transaction.processed_at = datetime.utcnow()

        # Update project status
        project.status = ProjectStatus.ACTIVE

        await db.commit()
        await db.refresh(transaction)

        logger.info(f"Escrow hold initiated: {transaction.id} for project {project.id}")

        return TransactionResponse.model_validate(transaction)

    except FinCraError as e:
        # Update transaction status to failed
        transaction.status = TransactionStatus.FAILED
        transaction.gateway_response = {
            "error": str(e),
            "status_code": e.status_code,
            "response_data": e.response_data,
        }
        await db.commit()

        logger.error(f"FinCra payment failed for transaction {transaction.id}: {e}")

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Payment processing failed: {e.message}",
        )

    except Exception as e:
        # Update transaction status to failed
        transaction.status = TransactionStatus.FAILED
        await db.commit()

        logger.error(f"Unexpected error during escrow hold: {e}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing the payment",
        )


@router.post("/release", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def release_escrow_funds(
    release_data: EscrowReleaseRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Release escrow funds for a completed and approved milestone.
    This transfers funds from escrow to the seller via FinCra.

    Args:
        release_data: Escrow release request data
        current_user: Currently authenticated user
        db: Database session

    Returns:
        Created transaction

    Raises:
        HTTPException: If milestone not found, not approved, or transfer fails
    """
    # Fetch milestone
    result = await db.execute(select(Milestone).where(Milestone.id == release_data.milestone_id))
    milestone = result.scalar_one_or_none()

    if not milestone:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Milestone not found")

    # Check if milestone is approved
    if milestone.status != MilestoneStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Milestone must be approved before funds can be released",
        )

    # Check if already paid
    if milestone.is_paid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Milestone has already been paid"
        )

    # Fetch project
    project_result = await db.execute(select(Project).where(Project.id == milestone.project_id))
    project = project_result.scalar_one_or_none()

    # Only buyer or admin can release funds
    if project.buyer_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Only the buyer can release escrow funds"
        )

    # Calculate release amount (no fee on release, fee was taken on hold)
    release_amount = milestone.amount

    # Create transaction record
    transaction = Transaction(
        user_id=project.seller_id if project.seller_id else current_user.id,
        project_id=project.id,
        transaction_type=TransactionType.ESCROW_RELEASE,
        status=TransactionStatus.PENDING,
        amount=release_amount,
        currency=milestone.currency,
        fee=0,  # Fee already taken during escrow hold
        net_amount=release_amount,
        payment_gateway="fincra",
        description=f"Escrow release for milestone: {milestone.title}",
        notes=release_data.notes,
    )

    db.add(transaction)
    await db.commit()
    await db.refresh(transaction)

    # Process transfer via FinCra
    try:
        fincra_client = get_fincra_client()

        # Fetch seller user for account details
        seller_result = await db.execute(select(User).where(User.id == project.seller_id))
        seller = seller_result.scalar_one_or_none()

        if not seller:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Seller not found for this project"
            )

        # Note: In production, you would have seller's bank account details stored
        # For now, we'll simulate with placeholder values
        transfer_response = await fincra_client.create_transfer(
            amount=release_amount,
            currency=milestone.currency,
            recipient_account="SELLER_ACCOUNT_NUMBER",  # Should come from seller profile
            recipient_bank_code="SELLER_BANK_CODE",  # Should come from seller profile
            reference=str(transaction.id),
            narration=f"Payment for milestone: {milestone.title}",
            metadata={
                "project_id": str(project.id),
                "milestone_id": str(milestone.id),
                "transaction_type": "escrow_release",
            },
        )

        # Update transaction with FinCra response
        transaction.status = TransactionStatus.PROCESSING
        transaction.gateway_transaction_id = transfer_response.get("data", {}).get("id")
        transaction.gateway_reference = transfer_response.get("data", {}).get("reference")
        transaction.gateway_response = transfer_response
        transaction.processed_at = datetime.utcnow()

        # Mark milestone as paid
        milestone.is_paid = True
        milestone.paid_at = datetime.utcnow()

        await db.commit()
        await db.refresh(transaction)

        logger.info(f"Escrow release initiated: {transaction.id} for milestone {milestone.id}")

        return TransactionResponse.model_validate(transaction)

    except FinCraError as e:
        # Update transaction status to failed
        transaction.status = TransactionStatus.FAILED
        transaction.gateway_response = {
            "error": str(e),
            "status_code": e.status_code,
            "response_data": e.response_data,
        }
        await db.commit()

        logger.error(f"FinCra transfer failed for transaction {transaction.id}: {e}")

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Transfer processing failed: {e.message}",
        )

    except Exception as e:
        # Update transaction status to failed
        transaction.status = TransactionStatus.FAILED
        await db.commit()

        logger.error(f"Unexpected error during escrow release: {e}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing the transfer",
        )


@router.get("/transactions", response_model=TransactionListResponse)
async def list_transactions(
    project_id: Optional[UUID] = Query(None, description="Filter by project ID"),
    transaction_type: Optional[TransactionType] = Query(
        None, description="Filter by transaction type"
    ),
    status_filter: Optional[TransactionStatus] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List transactions for the current user.

    Args:
        project_id: Optional project ID filter
        transaction_type: Optional transaction type filter
        status_filter: Optional status filter
        page: Page number
        page_size: Items per page
        current_user: Currently authenticated user
        db: Database session

    Returns:
        Paginated list of transactions
    """
    # Build query - show transactions for user's projects
    if current_user.is_superuser:
        # Admin can see all transactions
        query = select(Transaction)
    else:
        # Regular users can only see their own transactions
        query = select(Transaction).where(Transaction.user_id == current_user.id)

    # Apply filters
    if project_id:
        query = query.where(Transaction.project_id == project_id)
    if transaction_type:
        query = query.where(Transaction.transaction_type == transaction_type)
    if status_filter:
        query = query.where(Transaction.status == status_filter)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Apply pagination and ordering (most recent first)
    query = query.order_by(Transaction.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size + 1)

    # Execute query
    result = await db.execute(query)
    transactions = result.scalars().all()

    # Check if there are more items
    has_more = len(transactions) > page_size
    items = transactions[:page_size]

    return TransactionListResponse(
        items=[TransactionResponse.model_validate(t) for t in items],
        total=total,
        page=page,
        page_size=page_size,
        has_more=has_more,
    )


@router.get("/transactions/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific transaction by ID.

    Args:
        transaction_id: Transaction UUID
        current_user: Currently authenticated user
        db: Database session

    Returns:
        Transaction details

    Raises:
        HTTPException: If transaction not found or user not authorized
    """
    # Fetch transaction
    result = await db.execute(select(Transaction).where(Transaction.id == transaction_id))
    transaction = result.scalar_one_or_none()

    if not transaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")

    # Check if user has access (only admin or transaction owner)
    if not current_user.is_superuser and transaction.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this transaction",
        )

    return TransactionResponse.model_validate(transaction)
