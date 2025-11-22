"""
CRUD operations for Project model.
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
from app.models.project import Project, ProjectStatus


async def create_project(
    db: AsyncSession,
    title: str,
    description: str,
    total_amount: Decimal,
    creator_id: UUID,
    currency: str = "USD",
    buyer_id: Optional[UUID] = None,
    seller_id: Optional[UUID] = None,
    status: ProjectStatus = ProjectStatus.DRAFT,
    completion_criteria: Optional[str] = None,
    due_date: Optional[datetime] = None,
    start_date: Optional[datetime] = None,
) -> Project:
    """
    Create a new project.

    Args:
        db: Database session
        title: Project title
        description: Project description
        total_amount: Total project amount
        creator_id: Creator user ID
        currency: Currency code (default: USD)
        buyer_id: Buyer user ID
        seller_id: Seller user ID
        status: Project status
        completion_criteria: Project completion criteria
        due_date: Project due date
        start_date: Project start date

    Returns:
        Created project object

    Raises:
        BadRequestError: If validation fails
        ConflictError: If database constraint violated
    """
    try:
        if total_amount <= 0:
            raise BadRequestError("Total amount must be greater than zero")

        new_project = Project(
            title=title,
            description=description,
            total_amount=total_amount,
            creator_id=creator_id,
            currency=currency,
            buyer_id=buyer_id,
            seller_id=seller_id,
            status=status,
            completion_criteria=completion_criteria,
            due_date=due_date,
            start_date=start_date,
        )

        db.add(new_project)
        await db.commit()
        await db.refresh(new_project)

        return new_project
    except IntegrityError as e:
        await db.rollback()
        if "foreign key" in str(e.orig).lower():
            raise BadRequestError("Invalid user ID provided (creator, buyer, or seller)")
        raise ConflictError("Project creation failed due to database constraint violation")
    except Exception as e:
        if isinstance(e, (BadRequestError, ConflictError)):
            raise
        await db.rollback()
        raise


async def get_project_by_id(db: AsyncSession, project_id: UUID) -> Project:
    """
    Get a project by ID.

    Args:
        db: Database session
        project_id: Project UUID

    Returns:
        Project object

    Raises:
        NotFoundError: If project not found
    """
    try:
        result = await db.execute(select(Project).where(Project.id == project_id))
        project = result.scalar_one_or_none()

        if project is None:
            raise NotFoundError(f"Project with ID {project_id} not found")

        return project
    except Exception as e:
        if isinstance(e, NotFoundError):
            raise
        await db.rollback()
        raise


async def get_projects(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    status: Optional[ProjectStatus] = None,
    creator_id: Optional[UUID] = None,
    buyer_id: Optional[UUID] = None,
    seller_id: Optional[UUID] = None,
) -> List[Project]:
    """
    Get a list of projects with optional filtering.

    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        status: Filter by project status
        creator_id: Filter by creator ID
        buyer_id: Filter by buyer ID
        seller_id: Filter by seller ID

    Returns:
        List of project objects
    """
    try:
        query = select(Project)

        if status is not None:
            query = query.where(Project.status == status)

        if creator_id is not None:
            query = query.where(Project.creator_id == creator_id)

        if buyer_id is not None:
            query = query.where(Project.buyer_id == buyer_id)

        if seller_id is not None:
            query = query.where(Project.seller_id == seller_id)

        query = query.offset(skip).limit(limit)

        result = await db.execute(query)
        return list(result.scalars().all())
    except Exception:
        await db.rollback()
        raise


async def update_project(db: AsyncSession, project_id: UUID, **kwargs) -> Project:
    """
    Update a project.

    Args:
        db: Database session
        project_id: Project UUID
        **kwargs: Fields to update

    Returns:
        Updated project object

    Raises:
        NotFoundError: If project not found
        BadRequestError: If validation fails
        ConflictError: If update violates constraints
    """
    try:
        # Check if project exists
        project = await get_project_by_id(db, project_id)

        # Filter out None values and non-updatable fields
        update_data = {k: v for k, v in kwargs.items() if v is not None and k != "id"}

        if not update_data:
            return project

        # Validate total_amount if provided
        if "total_amount" in update_data and update_data["total_amount"] <= 0:
            raise BadRequestError("Total amount must be greater than zero")

        # Update project
        stmt = update(Project).where(Project.id == project_id).values(**update_data)
        await db.execute(stmt)
        await db.commit()
        await db.refresh(project)

        return project
    except IntegrityError as e:
        await db.rollback()
        if "foreign key" in str(e.orig).lower():
            raise BadRequestError("Invalid user ID provided")
        raise ConflictError("Update failed due to database constraint violation")
    except Exception as e:
        if isinstance(e, (NotFoundError, BadRequestError, ConflictError)):
            raise
        await db.rollback()
        raise


async def delete_project(db: AsyncSession, project_id: UUID) -> bool:
    """
    Delete a project.

    Args:
        db: Database session
        project_id: Project UUID

    Returns:
        True if deleted successfully

    Raises:
        NotFoundError: If project not found
    """
    try:
        # Check if project exists
        await get_project_by_id(db, project_id)

        # Delete project (cascades to milestones and transactions)
        stmt = delete(Project).where(Project.id == project_id)
        result = await db.execute(stmt)
        await db.commit()

        return result.rowcount > 0
    except Exception as e:
        if isinstance(e, NotFoundError):
            raise
        await db.rollback()
        raise


async def get_projects_by_user(
    db: AsyncSession,
    user_id: UUID,
    skip: int = 0,
    limit: int = 100,
    status: Optional[ProjectStatus] = None,
) -> List[Project]:
    """
    Get all projects associated with a user (as creator, buyer, or seller).

    Args:
        db: Database session
        user_id: User UUID
        skip: Number of records to skip
        limit: Maximum number of records to return
        status: Filter by project status

    Returns:
        List of project objects
    """
    try:
        query = select(Project).where(
            (Project.creator_id == user_id)
            | (Project.buyer_id == user_id)
            | (Project.seller_id == user_id)
        )

        if status is not None:
            query = query.where(Project.status == status)

        query = query.offset(skip).limit(limit)

        result = await db.execute(query)
        return list(result.scalars().all())
    except Exception:
        await db.rollback()
        raise
