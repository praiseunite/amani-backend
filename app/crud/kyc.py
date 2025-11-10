"""
CRUD operations for KYC model.
Includes error handling and session management.
"""
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from passlib.context import CryptContext

from app.models.kyc import Kyc, KycStatus, KycType
from app.core.exceptions import NotFoundError, ConflictError, BadRequestError

# Password hashing context for security codes
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_security_code(security_code: str) -> str:
    """
    Hash a security code using bcrypt.

    Args:
        security_code: Plain text security code

    Returns:
        Hashed security code
    """
    return pwd_context.hash(security_code)


def hash_approval_code(approval_code: str) -> str:
    """
    Hash an approval code using bcrypt.

    Args:
        approval_code: Plain text approval code

    Returns:
        Hashed approval code
    """
    return pwd_context.hash(approval_code)


async def create_kyc_submission(
    db: AsyncSession,
    user_id: UUID,
    nin_or_passport: str,
    security_code: str,
    type: KycType = KycType.KYC,
    fingerprint: Optional[bytes] = None,
    image: Optional[bytes] = None
) -> Kyc:
    """
    Create a new KYC submission.

    Args:
        db: Database session
        user_id: User UUID
        nin_or_passport: National ID or Passport number
        security_code: Security code (will be hashed)
        type: KYC type (KYC or KYB)
        fingerprint: Optional fingerprint biometric data
        image: Optional identity document image

    Returns:
        Created KYC object

    Raises:
        BadRequestError: If validation fails
        ConflictError: If user already has a pending or approved KYC
    """
    try:
        # Check if user already has a pending or approved KYC
        existing_kyc = await db.execute(
            select(Kyc).where(
                Kyc.user_id == user_id,
                Kyc.status.in_([KycStatus.PENDING, KycStatus.APPROVED])
            )
        )
        existing = existing_kyc.scalar_one_or_none()

        if existing:
            raise ConflictError(
                f"User already has a {existing.status.value} KYC submission"
            )

        # Hash the security code before storage
        hashed_security_code = hash_security_code(security_code)

        # Create new KYC submission
        new_kyc = Kyc(
            user_id=user_id,
            type=type,
            nin_or_passport=nin_or_passport,
            security_code=hashed_security_code,
            fingerprint=fingerprint,
            image=image,
            status=KycStatus.PENDING,
            submitted_at=datetime.utcnow()
        )

        db.add(new_kyc)
        await db.commit()
        await db.refresh(new_kyc)

        return new_kyc
    except IntegrityError as e:
        await db.rollback()
        if "foreign key" in str(e.orig).lower():
            raise BadRequestError("Invalid user ID provided")
        if "unique constraint" in str(e.orig).lower():
            raise ConflictError("KYC submission with this NIN/Passport already exists")
        raise ConflictError("KYC submission failed due to database constraint violation")
    except Exception as e:
        if isinstance(e, (BadRequestError, ConflictError)):
            raise
        await db.rollback()
        raise


async def get_kyc_by_user(
    db: AsyncSession,
    user_id: UUID,
    status: Optional[KycStatus] = None
) -> List[Kyc]:
    """
    Get KYC records for a specific user.

    Args:
        db: Database session
        user_id: User UUID
        status: Optional status filter

    Returns:
        List of KYC objects for the user
    """
    try:
        query = select(Kyc).where(Kyc.user_id == user_id)

        if status is not None:
            query = query.where(Kyc.status == status)

        query = query.order_by(Kyc.submitted_at.desc())

        result = await db.execute(query)
        return list(result.scalars().all())
    except Exception:
        await db.rollback()
        raise


async def get_kyc_by_id(db: AsyncSession, kyc_id: UUID) -> Kyc:
    """
    Get a KYC record by ID.

    Args:
        db: Database session
        kyc_id: KYC UUID

    Returns:
        KYC object

    Raises:
        NotFoundError: If KYC record not found
    """
    try:
        result = await db.execute(
            select(Kyc).where(Kyc.id == kyc_id)
        )
        kyc = result.scalar_one_or_none()

        if kyc is None:
            raise NotFoundError(f"KYC record with ID {kyc_id} not found")

        return kyc
    except Exception as e:
        if isinstance(e, NotFoundError):
            raise
        await db.rollback()
        raise


async def update_kyc_status(
    db: AsyncSession,
    kyc_id: UUID,
    status: KycStatus,
    rejection_reason: Optional[str] = None,
    approval_code: Optional[str] = None
) -> Kyc:
    """
    Update KYC status (for admin approval/rejection).

    Args:
        db: Database session
        kyc_id: KYC UUID
        status: New status (APPROVED or REJECTED)
        rejection_reason: Reason for rejection (required if status is REJECTED)
        approval_code: Approval code for clients (required if status is APPROVED, will be hashed)

    Returns:
        Updated KYC object

    Raises:
        NotFoundError: If KYC record not found
        BadRequestError: If validation fails
    """
    try:
        # Check if KYC exists
        kyc = await get_kyc_by_id(db, kyc_id)

        # Validate status transition
        if status == KycStatus.REJECTED and not rejection_reason:
            raise BadRequestError("Rejection reason is required when rejecting KYC")

        if status == KycStatus.APPROVED and not approval_code:
            raise BadRequestError("Approval code is required when approving KYC")

        # Prepare update data
        update_data = {
            "status": status,
            "updated_at": datetime.utcnow()
        }

        if status == KycStatus.APPROVED:
            update_data["verified_at"] = datetime.utcnow()
            update_data["approval_code"] = hash_approval_code(approval_code)
            update_data["rejection_reason"] = None  # Clear any previous rejection reason
        elif status == KycStatus.REJECTED:
            update_data["rejection_reason"] = rejection_reason
            update_data["verified_at"] = None
            update_data["approval_code"] = None

        # Update KYC
        stmt = update(Kyc).where(Kyc.id == kyc_id).values(**update_data)
        await db.execute(stmt)
        await db.commit()
        await db.refresh(kyc)

        return kyc
    except Exception as e:
        if isinstance(e, (NotFoundError, BadRequestError)):
            raise
        await db.rollback()
        raise


async def get_all_kyc_submissions(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    status: Optional[KycStatus] = None,
    type: Optional[KycType] = None
) -> List[Kyc]:
    """
    Get all KYC submissions with optional filtering (admin only).

    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        status: Filter by status
        type: Filter by type (KYC or KYB)

    Returns:
        List of KYC objects
    """
    try:
        query = select(Kyc)

        if status is not None:
            query = query.where(Kyc.status == status)

        if type is not None:
            query = query.where(Kyc.type == type)

        query = query.order_by(Kyc.submitted_at.desc()).offset(skip).limit(limit)

        result = await db.execute(query)
        return list(result.scalars().all())
    except Exception:
        await db.rollback()
        raise
