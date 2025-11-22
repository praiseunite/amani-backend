"""
CRUD operations for Milestone model.
Includes error handling and session management.
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, ConflictError, NotFoundError
from app.models.milestone import Milestone, MilestoneStatus


async def create_milestone(
    db: AsyncSession,
    project_id: UUID,
    title: str,
    description: str,
    amount: Decimal,
    currency: str = "USD",
    status: MilestoneStatus = MilestoneStatus.PENDING,
    order_index: int = 0,
    completion_criteria: Optional[str] = None,
    due_date: Optional[datetime] = None,
) -> Milestone:
    """
    Create a new milestone.

    Args:
        db: Database session
        project_id: Project ID this milestone belongs to
        title: Milestone title
        description: Milestone description
        amount: Milestone amount
        currency: Currency code (default: USD)
        status: Milestone status
        order_index: Order/sequence of the milestone
        completion_criteria: Milestone completion criteria
        due_date: Milestone due date

    Returns:
        Created milestone object

    Raises:
        BadRequestError: If validation fails
        ConflictError: If database constraint violated
    """
    try:
        if amount <= 0:
            raise BadRequestError("Amount must be greater than zero")

        new_milestone = Milestone(
            project_id=project_id,
            title=title,
            description=description,
            amount=amount,
            currency=currency,
            status=status,
            order_index=order_index,
            completion_criteria=completion_criteria,
            due_date=due_date,
        )

        db.add(new_milestone)
        await db.commit()
        await db.refresh(new_milestone)

        return new_milestone
    except IntegrityError as e:
        await db.rollback()
        if "foreign key" in str(e.orig).lower():
            raise BadRequestError(f"Project with ID {project_id} not found")
        raise ConflictError("Milestone creation failed due to database constraint violation")
    except Exception as e:
        if isinstance(e, (BadRequestError, ConflictError)):
            raise
        await db.rollback()
        raise


async def get_milestone_by_id(db: AsyncSession, milestone_id: UUID) -> Milestone:
    """
    Get a milestone by ID.

    Args:
        db: Database session
        milestone_id: Milestone UUID

    Returns:
        Milestone object

    Raises:
        NotFoundError: If milestone not found
    """
    try:
        result = await db.execute(select(Milestone).where(Milestone.id == milestone_id))
        milestone = result.scalar_one_or_none()

        if milestone is None:
            raise NotFoundError(f"Milestone with ID {milestone_id} not found")

        return milestone
    except Exception as e:
        if isinstance(e, NotFoundError):
            raise
        await db.rollback()
        raise


async def get_milestones(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    project_id: Optional[UUID] = None,
    status: Optional[MilestoneStatus] = None,
) -> List[Milestone]:
    """
    Get a list of milestones with optional filtering.

    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        project_id: Filter by project ID
        status: Filter by milestone status

    Returns:
        List of milestone objects
    """
    try:
        query = select(Milestone)

        if project_id is not None:
            query = query.where(Milestone.project_id == project_id)

        if status is not None:
            query = query.where(Milestone.status == status)

        query = query.order_by(Milestone.order_index).offset(skip).limit(limit)

        result = await db.execute(query)
        return list(result.scalars().all())
    except Exception:
        await db.rollback()
        raise


async def get_milestones_by_project(
    db: AsyncSession, project_id: UUID, skip: int = 0, limit: int = 100
) -> List[Milestone]:
    """
    Get all milestones for a specific project.

    Args:
        db: Database session
        project_id: Project UUID
        skip: Number of records to skip
        limit: Maximum number of records to return

    Returns:
        List of milestone objects ordered by order_index
    """
    return await get_milestones(db, skip=skip, limit=limit, project_id=project_id)


async def update_milestone(db: AsyncSession, milestone_id: UUID, **kwargs) -> Milestone:
    """
    Update a milestone.

    Args:
        db: Database session
        milestone_id: Milestone UUID
        **kwargs: Fields to update

    Returns:
        Updated milestone object

    Raises:
        NotFoundError: If milestone not found
        BadRequestError: If validation fails
        ConflictError: If update violates constraints
    """
    try:
        # Check if milestone exists
        milestone = await get_milestone_by_id(db, milestone_id)

        # Filter out None values and non-updatable fields
        update_data = {k: v for k, v in kwargs.items() if v is not None and k != "id"}

        if not update_data:
            return milestone

        # Validate amount if provided
        if "amount" in update_data and update_data["amount"] <= 0:
            raise BadRequestError("Amount must be greater than zero")

        # Update milestone
        stmt = update(Milestone).where(Milestone.id == milestone_id).values(**update_data)
        await db.execute(stmt)
        await db.commit()
        await db.refresh(milestone)

        return milestone
    except IntegrityError as e:
        await db.rollback()
        if "foreign key" in str(e.orig).lower():
            raise BadRequestError("Invalid project ID provided")
        raise ConflictError("Update failed due to database constraint violation")
    except Exception as e:
        if isinstance(e, (NotFoundError, BadRequestError, ConflictError)):
            raise
        await db.rollback()
        raise


async def delete_milestone(db: AsyncSession, milestone_id: UUID) -> bool:
    """
    Delete a milestone.

    Args:
        db: Database session
        milestone_id: Milestone UUID

    Returns:
        True if deleted successfully

    Raises:
        NotFoundError: If milestone not found
    """
    try:
        # Check if milestone exists
        await get_milestone_by_id(db, milestone_id)

        # Delete milestone
        stmt = delete(Milestone).where(Milestone.id == milestone_id)
        result = await db.execute(stmt)
        await db.commit()

        return result.rowcount > 0
    except Exception as e:
        if isinstance(e, NotFoundError):
            raise
        await db.rollback()
        raise


async def mark_milestone_completed(
    db: AsyncSession, milestone_id: UUID, completion_notes: Optional[str] = None
) -> Milestone:
    """
    Mark a milestone as completed.

    Args:
        db: Database session
        milestone_id: Milestone UUID
        completion_notes: Optional notes about completion

    Returns:
        Updated milestone object

    Raises:
        NotFoundError: If milestone not found
    """
    update_data = {"status": MilestoneStatus.COMPLETED, "completed_at": datetime.utcnow()}

    if completion_notes:
        update_data["completion_notes"] = completion_notes

    return await update_milestone(db, milestone_id, **update_data)


async def mark_milestone_approved(db: AsyncSession, milestone_id: UUID) -> Milestone:
    """
    Mark a milestone as approved.

    Args:
        db: Database session
        milestone_id: Milestone UUID

    Returns:
        Updated milestone object

    Raises:
        NotFoundError: If milestone not found
    """
    update_data = {"status": MilestoneStatus.APPROVED, "approved_at": datetime.utcnow()}

    return await update_milestone(db, milestone_id, **update_data)


async def mark_milestone_paid(db: AsyncSession, milestone_id: UUID) -> Milestone:
    """
    Mark a milestone as paid.

    Args:
        db: Database session
        milestone_id: Milestone UUID

    Returns:
        Updated milestone object

    Raises:
        NotFoundError: If milestone not found
    """
    update_data = {"is_paid": True, "paid_at": datetime.utcnow()}

    return await update_milestone(db, milestone_id, **update_data)
