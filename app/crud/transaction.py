"""
CRUD operations for Transaction model.
Includes error handling and session management.
"""
from typing import Optional, List, Dict, Any
from uuid import UUID
from decimal import Decimal
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.exc import IntegrityError

from app.models.transaction import Transaction, TransactionType, TransactionStatus
from app.core.exceptions import NotFoundError, ConflictError, BadRequestError


async def create_transaction(
    db: AsyncSession,
    user_id: UUID,
    transaction_type: TransactionType,
    amount: Decimal,
    currency: str = "USD",
    project_id: Optional[UUID] = None,
    status: TransactionStatus = TransactionStatus.PENDING,
    fee: Decimal = Decimal("0"),
    net_amount: Optional[Decimal] = None,
    description: Optional[str] = None,
    payment_gateway: str = "fincra",
    gateway_transaction_id: Optional[str] = None,
    gateway_reference: Optional[str] = None,
    gateway_response: Optional[Dict[str, Any]] = None,
    notes: Optional[str] = None,
    extra_data: Optional[Dict[str, Any]] = None
) -> Transaction:
    """
    Create a new transaction.
    
    Args:
        db: Database session
        user_id: User ID associated with transaction
        transaction_type: Type of transaction
        amount: Transaction amount
        currency: Currency code (default: USD)
        project_id: Optional project ID
        status: Transaction status
        fee: Transaction fee
        net_amount: Net amount (calculated if not provided)
        description: Transaction description
        payment_gateway: Payment gateway name
        gateway_transaction_id: Gateway transaction ID
        gateway_reference: Gateway reference
        gateway_response: Gateway response data
        notes: Additional notes
        extra_data: Extra metadata
        
    Returns:
        Created transaction object
        
    Raises:
        BadRequestError: If validation fails
        ConflictError: If database constraint violated
    """
    try:
        if amount <= 0:
            raise BadRequestError("Amount must be greater than zero")
        
        if fee < 0:
            raise BadRequestError("Fee cannot be negative")
        
        # Calculate net_amount if not provided
        if net_amount is None:
            net_amount = amount - fee
        
        new_transaction = Transaction(
            user_id=user_id,
            transaction_type=transaction_type,
            amount=amount,
            currency=currency,
            project_id=project_id,
            status=status,
            fee=fee,
            net_amount=net_amount,
            description=description,
            payment_gateway=payment_gateway,
            gateway_transaction_id=gateway_transaction_id,
            gateway_reference=gateway_reference,
            gateway_response=gateway_response,
            notes=notes,
            extra_data=extra_data
        )
        
        db.add(new_transaction)
        await db.commit()
        await db.refresh(new_transaction)
        
        return new_transaction
    except IntegrityError as e:
        await db.rollback()
        if "foreign key" in str(e.orig).lower():
            raise BadRequestError("Invalid user ID or project ID provided")
        if "unique constraint" in str(e.orig).lower() and "gateway_transaction_id" in str(e.orig).lower():
            raise ConflictError(f"Transaction with gateway ID {gateway_transaction_id} already exists")
        raise ConflictError("Transaction creation failed due to database constraint violation")
    except Exception as e:
        if isinstance(e, (BadRequestError, ConflictError)):
            raise
        await db.rollback()
        raise


async def get_transaction_by_id(db: AsyncSession, transaction_id: UUID) -> Transaction:
    """
    Get a transaction by ID.
    
    Args:
        db: Database session
        transaction_id: Transaction UUID
        
    Returns:
        Transaction object
        
    Raises:
        NotFoundError: If transaction not found
    """
    try:
        result = await db.execute(
            select(Transaction).where(Transaction.id == transaction_id)
        )
        transaction = result.scalar_one_or_none()
        
        if transaction is None:
            raise NotFoundError(f"Transaction with ID {transaction_id} not found")
        
        return transaction
    except Exception as e:
        if isinstance(e, NotFoundError):
            raise
        await db.rollback()
        raise


async def get_transaction_by_gateway_id(
    db: AsyncSession,
    gateway_transaction_id: str
) -> Optional[Transaction]:
    """
    Get a transaction by gateway transaction ID.
    
    Args:
        db: Database session
        gateway_transaction_id: Gateway transaction ID
        
    Returns:
        Transaction object or None if not found
    """
    try:
        result = await db.execute(
            select(Transaction).where(
                Transaction.gateway_transaction_id == gateway_transaction_id
            )
        )
        return result.scalar_one_or_none()
    except Exception:
        await db.rollback()
        raise


async def get_transactions(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[UUID] = None,
    project_id: Optional[UUID] = None,
    transaction_type: Optional[TransactionType] = None,
    status: Optional[TransactionStatus] = None
) -> List[Transaction]:
    """
    Get a list of transactions with optional filtering.
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        user_id: Filter by user ID
        project_id: Filter by project ID
        transaction_type: Filter by transaction type
        status: Filter by transaction status
        
    Returns:
        List of transaction objects
    """
    try:
        query = select(Transaction)
        
        if user_id is not None:
            query = query.where(Transaction.user_id == user_id)
        
        if project_id is not None:
            query = query.where(Transaction.project_id == project_id)
        
        if transaction_type is not None:
            query = query.where(Transaction.transaction_type == transaction_type)
        
        if status is not None:
            query = query.where(Transaction.status == status)
        
        query = query.order_by(Transaction.created_at.desc()).offset(skip).limit(limit)
        
        result = await db.execute(query)
        return list(result.scalars().all())
    except Exception:
        await db.rollback()
        raise


async def get_transactions_by_user(
    db: AsyncSession,
    user_id: UUID,
    skip: int = 0,
    limit: int = 100,
    status: Optional[TransactionStatus] = None
) -> List[Transaction]:
    """
    Get all transactions for a specific user.
    
    Args:
        db: Database session
        user_id: User UUID
        skip: Number of records to skip
        limit: Maximum number of records to return
        status: Filter by transaction status
        
    Returns:
        List of transaction objects
    """
    return await get_transactions(db, skip=skip, limit=limit, user_id=user_id, status=status)


async def get_transactions_by_project(
    db: AsyncSession,
    project_id: UUID,
    skip: int = 0,
    limit: int = 100,
    status: Optional[TransactionStatus] = None
) -> List[Transaction]:
    """
    Get all transactions for a specific project.
    
    Args:
        db: Database session
        project_id: Project UUID
        skip: Number of records to skip
        limit: Maximum number of records to return
        status: Filter by transaction status
        
    Returns:
        List of transaction objects
    """
    return await get_transactions(db, skip=skip, limit=limit, project_id=project_id, status=status)


async def update_transaction(
    db: AsyncSession,
    transaction_id: UUID,
    **kwargs
) -> Transaction:
    """
    Update a transaction.
    
    Args:
        db: Database session
        transaction_id: Transaction UUID
        **kwargs: Fields to update
        
    Returns:
        Updated transaction object
        
    Raises:
        NotFoundError: If transaction not found
        BadRequestError: If validation fails
        ConflictError: If update violates constraints
    """
    try:
        # Check if transaction exists
        transaction = await get_transaction_by_id(db, transaction_id)
        
        # Filter out None values and non-updatable fields
        update_data = {k: v for k, v in kwargs.items() if v is not None and k != 'id'}
        
        if not update_data:
            return transaction
        
        # Validate amount if provided
        if 'amount' in update_data and update_data['amount'] <= 0:
            raise BadRequestError("Amount must be greater than zero")
        
        if 'fee' in update_data and update_data['fee'] < 0:
            raise BadRequestError("Fee cannot be negative")
        
        # Update transaction
        stmt = update(Transaction).where(Transaction.id == transaction_id).values(**update_data)
        await db.execute(stmt)
        await db.commit()
        await db.refresh(transaction)
        
        return transaction
    except IntegrityError as e:
        await db.rollback()
        if "foreign key" in str(e.orig).lower():
            raise BadRequestError("Invalid user ID or project ID provided")
        if "unique constraint" in str(e.orig).lower():
            raise ConflictError("Update failed due to unique constraint violation")
        raise ConflictError("Update failed due to database constraint violation")
    except Exception as e:
        if isinstance(e, (NotFoundError, BadRequestError, ConflictError)):
            raise
        await db.rollback()
        raise


async def delete_transaction(db: AsyncSession, transaction_id: UUID) -> bool:
    """
    Delete a transaction.
    
    Args:
        db: Database session
        transaction_id: Transaction UUID
        
    Returns:
        True if deleted successfully
        
    Raises:
        NotFoundError: If transaction not found
    """
    try:
        # Check if transaction exists
        await get_transaction_by_id(db, transaction_id)
        
        # Delete transaction
        stmt = delete(Transaction).where(Transaction.id == transaction_id)
        result = await db.execute(stmt)
        await db.commit()
        
        return result.rowcount > 0
    except Exception as e:
        if isinstance(e, NotFoundError):
            raise
        await db.rollback()
        raise


async def update_transaction_status(
    db: AsyncSession,
    transaction_id: UUID,
    status: TransactionStatus,
    gateway_response: Optional[Dict[str, Any]] = None
) -> Transaction:
    """
    Update transaction status.
    
    Args:
        db: Database session
        transaction_id: Transaction UUID
        status: New transaction status
        gateway_response: Optional gateway response data
        
    Returns:
        Updated transaction object
        
    Raises:
        NotFoundError: If transaction not found
    """
    update_data = {"status": status}
    
    # Set timestamps based on status
    if status == TransactionStatus.PROCESSING:
        update_data["processed_at"] = datetime.utcnow()
    elif status == TransactionStatus.COMPLETED:
        update_data["completed_at"] = datetime.utcnow()
        if not update_data.get("processed_at"):
            update_data["processed_at"] = datetime.utcnow()
    
    if gateway_response:
        update_data["gateway_response"] = gateway_response
    
    return await update_transaction(db, transaction_id, **update_data)
