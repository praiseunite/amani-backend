"""
Milestone routes for tracking project progress.
"""

from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from uuid import UUID
import logging

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.models.project import Project
from app.models.milestone import Milestone, MilestoneStatus
from app.schemas.milestone import (
    MilestoneCreate,
    MilestoneUpdate,
    MilestoneSubmit,
    MilestoneApprove,
    MilestoneResponse,
    MilestoneListResponse,
)


router = APIRouter(prefix="/milestones", tags=["milestones"])
logger = logging.getLogger(__name__)


@router.post("", response_model=MilestoneResponse, status_code=status.HTTP_201_CREATED)
async def create_milestone(
    milestone_data: MilestoneCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new milestone for a project.

    Args:
        milestone_data: Milestone creation data
        current_user: Currently authenticated user
        db: Database session

    Returns:
        Created milestone

    Raises:
        HTTPException: If project not found or user not authorized
    """
    # Fetch project
    result = await db.execute(select(Project).where(Project.id == milestone_data.project_id))
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    # Check if user is project creator or seller
    if project.creator_id != current_user.id and project.seller_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only project creator or seller can create milestones",
        )

    # Create new milestone
    new_milestone = Milestone(
        project_id=milestone_data.project_id,
        title=milestone_data.title,
        description=milestone_data.description,
        amount=milestone_data.amount,
        currency=milestone_data.currency,
        completion_criteria=milestone_data.completion_criteria,
        due_date=milestone_data.due_date,
        order_index=milestone_data.order_index,
        status=MilestoneStatus.PENDING,
    )

    db.add(new_milestone)
    await db.commit()
    await db.refresh(new_milestone)

    logger.info(
        f"Milestone created: {new_milestone.id} for project {project.id} by user {current_user.email}"
    )

    return MilestoneResponse.model_validate(new_milestone)


@router.get("", response_model=MilestoneListResponse)
async def list_milestones(
    project_id: Optional[UUID] = Query(None, description="Filter by project ID"),
    status_filter: Optional[MilestoneStatus] = Query(
        None, description="Filter by milestone status"
    ),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List milestones for the current user's projects.

    Args:
        project_id: Optional project ID filter
        status_filter: Optional status filter
        page: Page number
        page_size: Items per page
        current_user: Currently authenticated user
        db: Database session

    Returns:
        Paginated list of milestones
    """
    # Build query - join with projects to filter by user
    query = (
        select(Milestone)
        .join(Project)
        .where(
            (Project.creator_id == current_user.id)
            | (Project.buyer_id == current_user.id)
            | (Project.seller_id == current_user.id)
        )
    )

    # Apply project filter if provided
    if project_id:
        query = query.where(Milestone.project_id == project_id)

    # Apply status filter if provided
    if status_filter:
        query = query.where(Milestone.status == status_filter)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Apply pagination
    query = query.offset((page - 1) * page_size).limit(page_size + 1)

    # Execute query
    result = await db.execute(query)
    milestones = result.scalars().all()

    # Check if there are more items
    has_more = len(milestones) > page_size
    items = milestones[:page_size]

    return MilestoneListResponse(
        items=[MilestoneResponse.model_validate(m) for m in items],
        total=total,
        page=page,
        page_size=page_size,
        has_more=has_more,
    )


@router.get("/{milestone_id}", response_model=MilestoneResponse)
async def get_milestone(
    milestone_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific milestone by ID.

    Args:
        milestone_id: Milestone UUID
        current_user: Currently authenticated user
        db: Database session

    Returns:
        Milestone details

    Raises:
        HTTPException: If milestone not found or user not authorized
    """
    # Fetch milestone with project
    result = await db.execute(select(Milestone).where(Milestone.id == milestone_id))
    milestone = result.scalar_one_or_none()

    if not milestone:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Milestone not found")

    # Fetch project to check access
    project_result = await db.execute(select(Project).where(Project.id == milestone.project_id))
    project = project_result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    # Check if user has access
    if (
        project.creator_id != current_user.id
        and project.buyer_id != current_user.id
        and project.seller_id != current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="You don't have access to this milestone"
        )

    return MilestoneResponse.model_validate(milestone)


@router.put("/{milestone_id}", response_model=MilestoneResponse)
async def update_milestone(
    milestone_id: UUID,
    milestone_update: MilestoneUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update a milestone.

    Args:
        milestone_id: Milestone UUID
        milestone_update: Updated milestone data
        current_user: Currently authenticated user
        db: Database session

    Returns:
        Updated milestone

    Raises:
        HTTPException: If milestone not found or user not authorized
    """
    # Fetch milestone
    result = await db.execute(select(Milestone).where(Milestone.id == milestone_id))
    milestone = result.scalar_one_or_none()

    if not milestone:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Milestone not found")

    # Fetch project
    project_result = await db.execute(select(Project).where(Project.id == milestone.project_id))
    project = project_result.scalar_one_or_none()

    # Only creator or seller can update milestone
    if project.creator_id != current_user.id and project.seller_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only project creator or seller can update milestones",
        )

    # Update fields
    if milestone_update.title is not None:
        milestone.title = milestone_update.title
    if milestone_update.description is not None:
        milestone.description = milestone_update.description
    if milestone_update.amount is not None:
        milestone.amount = milestone_update.amount
    if milestone_update.currency is not None:
        milestone.currency = milestone_update.currency
    if milestone_update.completion_criteria is not None:
        milestone.completion_criteria = milestone_update.completion_criteria
    if milestone_update.due_date is not None:
        milestone.due_date = milestone_update.due_date
    if milestone_update.order_index is not None:
        milestone.order_index = milestone_update.order_index
    if milestone_update.status is not None:
        milestone.status = milestone_update.status

    await db.commit()
    await db.refresh(milestone)

    logger.info(f"Milestone updated: {milestone_id} by user {current_user.email}")

    return MilestoneResponse.model_validate(milestone)


@router.post("/{milestone_id}/submit", response_model=MilestoneResponse)
async def submit_milestone(
    milestone_id: UUID,
    submit_data: MilestoneSubmit,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit a milestone for approval (seller action).

    Args:
        milestone_id: Milestone UUID
        submit_data: Submission data with completion notes
        current_user: Currently authenticated user
        db: Database session

    Returns:
        Updated milestone

    Raises:
        HTTPException: If milestone not found or user not authorized
    """
    # Fetch milestone
    result = await db.execute(select(Milestone).where(Milestone.id == milestone_id))
    milestone = result.scalar_one_or_none()

    if not milestone:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Milestone not found")

    # Fetch project
    project_result = await db.execute(select(Project).where(Project.id == milestone.project_id))
    project = project_result.scalar_one_or_none()

    # Only seller can submit milestone
    if project.seller_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Only the seller can submit milestones"
        )

    # Check milestone status
    if milestone.status not in [MilestoneStatus.PENDING, MilestoneStatus.IN_PROGRESS]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Milestone cannot be submitted in its current state",
        )

    # Update milestone
    milestone.status = MilestoneStatus.COMPLETED
    milestone.completion_notes = submit_data.completion_notes
    milestone.completed_at = datetime.utcnow()

    await db.commit()
    await db.refresh(milestone)

    logger.info(f"Milestone submitted: {milestone_id} by user {current_user.email}")

    return MilestoneResponse.model_validate(milestone)


@router.post("/{milestone_id}/approve", response_model=MilestoneResponse)
async def approve_milestone(
    milestone_id: UUID,
    approve_data: MilestoneApprove,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Approve or reject a milestone (buyer action).
    This endpoint will trigger the escrow release if approved.

    Args:
        milestone_id: Milestone UUID
        approve_data: Approval decision and notes
        current_user: Currently authenticated user
        db: Database session

    Returns:
        Updated milestone

    Raises:
        HTTPException: If milestone not found or user not authorized
    """
    # Fetch milestone
    result = await db.execute(select(Milestone).where(Milestone.id == milestone_id))
    milestone = result.scalar_one_or_none()

    if not milestone:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Milestone not found")

    # Fetch project
    project_result = await db.execute(select(Project).where(Project.id == milestone.project_id))
    project = project_result.scalar_one_or_none()

    # Only buyer can approve milestone
    if project.buyer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Only the buyer can approve milestones"
        )

    # Check milestone status
    if milestone.status != MilestoneStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only completed milestones can be approved or rejected",
        )

    # Update milestone
    if approve_data.approved:
        milestone.status = MilestoneStatus.APPROVED
        milestone.approved_at = datetime.utcnow()
        logger.info(f"Milestone approved: {milestone_id} by user {current_user.email}")
    else:
        milestone.status = MilestoneStatus.REJECTED
        logger.info(f"Milestone rejected: {milestone_id} by user {current_user.email}")

    if approve_data.notes:
        milestone.completion_notes = (
            f"{milestone.completion_notes}\n\n--- Buyer Notes ---\n{approve_data.notes}"
            if milestone.completion_notes
            else approve_data.notes
        )

    await db.commit()
    await db.refresh(milestone)

    return MilestoneResponse.model_validate(milestone)
