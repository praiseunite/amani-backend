"""
KYC routes for identity verification submission and status checking.
Integrates with FinCra API for KYC verification.
"""

import base64
import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.core.exceptions import BadRequestError, ConflictError, NotFoundError
from app.core.fincra import FinCraError, get_fincra_client
from app.crud.kyc import create_kyc_submission, get_kyc_by_id, get_kyc_by_user
from app.models.kyc import KycStatus
from app.models.user import User
from app.schemas.kyc import KycCreate, KycResponse

router = APIRouter(prefix="/kyc", tags=["kyc"])
logger = logging.getLogger(__name__)


@router.post("/submit", response_model=KycResponse, status_code=status.HTTP_201_CREATED)
async def submit_kyc(
    kyc_data: KycCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit KYC information for verification.

    Creates a KYC submission in the database and forwards it to FinCra for verification.
    Users can only submit KYC for themselves.

    Args:
        kyc_data: KYC submission data
        current_user: Currently authenticated user
        db: Database session

    Returns:
        Created KYC submission with status

    Raises:
        HTTPException: If submission fails or user already has pending/approved KYC
    """
    try:
        # Create KYC submission in database
        kyc_record = await create_kyc_submission(
            db=db,
            user_id=current_user.id,
            nin_or_passport=kyc_data.nin_or_passport,
            security_code=kyc_data.security_code,
            type=kyc_data.type,
            fingerprint=kyc_data.fingerprint,
            image=kyc_data.image,
        )

        # Submit to FinCra for verification
        try:
            fincra_client = get_fincra_client()

            # Prepare document image as base64 if provided
            document_image = None
            if kyc_data.image:
                document_image = base64.b64encode(kyc_data.image).decode("utf-8")

            # Submit to FinCra
            fincra_response = await fincra_client.submit_kyc(
                user_id=str(current_user.id),
                kyc_type=kyc_data.type.value,
                nin_or_passport=kyc_data.nin_or_passport,
                first_name=current_user.full_name.split()[0] if current_user.full_name else "",
                last_name=(
                    current_user.full_name.split()[-1]
                    if current_user.full_name and len(current_user.full_name.split()) > 1
                    else ""
                ),
                email=current_user.email,
                phone=getattr(current_user, "phone", None),
                document_image=document_image,
            )

            logger.info(f"KYC submitted to FinCra for user {current_user.id}: {fincra_response}")

        except FinCraError as e:
            logger.error(f"FinCra KYC submission failed: {e.message}")
            # Note: We keep the local DB record even if FinCra submission fails
            # This allows for manual review or retry

        # Return response
        return KycResponse.from_orm_with_flags(kyc_record)

    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except BadRequestError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"KYC submission error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit KYC information",
        )


@router.get("/status", response_model=List[KycResponse])
async def get_kyc_status(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    status_filter: Optional[KycStatus] = Query(None, description="Filter by KYC status"),
):
    """
    Get KYC submission status for the current user.

    Returns all KYC submissions for the authenticated user, optionally filtered by status.
    Users can only view their own KYC submissions.

    Args:
        current_user: Currently authenticated user
        db: Database session
        status_filter: Optional status filter

    Returns:
        List of user's KYC submissions

    Raises:
        HTTPException: If retrieval fails
    """
    try:
        # Get KYC records for current user
        kyc_records = await get_kyc_by_user(db=db, user_id=current_user.id, status=status_filter)

        # If user has active KYC and wants to check FinCra status
        if kyc_records and not status_filter:
            try:
                fincra_client = get_fincra_client()
                fincra_status = await fincra_client.get_kyc_status(str(current_user.id))
                logger.info(f"FinCra KYC status for user {current_user.id}: {fincra_status}")
            except FinCraError as e:
                logger.warning(f"Could not fetch FinCra KYC status: {e.message}")

        # Return response
        return [KycResponse.from_orm_with_flags(kyc) for kyc in kyc_records]

    except Exception as e:
        logger.error(f"KYC status retrieval error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve KYC status",
        )


@router.post("/resubmit/{kyc_id}", response_model=KycResponse)
async def resubmit_kyc(
    kyc_id: UUID,
    kyc_data: KycCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Resubmit a rejected KYC application with updated information.

    Allows users to update and resubmit their KYC information if it was previously rejected.
    Only the owner of the KYC submission can resubmit.

    Args:
        kyc_id: UUID of the rejected KYC submission
        kyc_data: Updated KYC submission data
        current_user: Currently authenticated user
        db: Database session

    Returns:
        New KYC submission

    Raises:
        HTTPException: If KYC not found, not rejected, or user not authorized
    """
    try:
        # Get existing KYC record
        try:
            existing_kyc = await get_kyc_by_id(db, kyc_id)
        except NotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="KYC submission not found"
            )

        # Verify ownership
        if existing_kyc.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="You can only resubmit your own KYC"
            )

        # Verify status is rejected
        if existing_kyc.status != KycStatus.REJECTED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only resubmit rejected KYC submissions",
            )

        # Create new KYC submission
        new_kyc = await create_kyc_submission(
            db=db,
            user_id=current_user.id,
            nin_or_passport=kyc_data.nin_or_passport,
            security_code=kyc_data.security_code,
            type=kyc_data.type,
            fingerprint=kyc_data.fingerprint,
            image=kyc_data.image,
        )

        # Submit to FinCra
        try:
            fincra_client = get_fincra_client()

            # Prepare document image as base64 if provided
            document_image = None
            if kyc_data.image:
                document_image = base64.b64encode(kyc_data.image).decode("utf-8")

            # Submit to FinCra
            fincra_response = await fincra_client.submit_kyc(
                user_id=str(current_user.id),
                kyc_type=kyc_data.type.value,
                nin_or_passport=kyc_data.nin_or_passport,
                first_name=current_user.full_name.split()[0] if current_user.full_name else "",
                last_name=(
                    current_user.full_name.split()[-1]
                    if current_user.full_name and len(current_user.full_name.split()) > 1
                    else ""
                ),
                email=current_user.email,
                phone=getattr(current_user, "phone", None),
                document_image=document_image,
            )

            logger.info(f"KYC resubmitted to FinCra for user {current_user.id}: {fincra_response}")

        except FinCraError as e:
            logger.error(f"FinCra KYC resubmission failed: {e.message}")

        return KycResponse.from_orm_with_flags(new_kyc)

    except HTTPException:
        raise
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except BadRequestError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"KYC resubmission error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resubmit KYC information",
        )
