"""
Project routes for escrow project management.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from uuid import UUID
import logging

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.models.project import Project, ProjectStatus
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse, ProjectListResponse


router = APIRouter(prefix="/projects", tags=["projects"])
logger = logging.getLogger(__name__)


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new escrow project.

    Args:
        project_data: Project creation data
        current_user: Currently authenticated user
        db: Database session

    Returns:
        Created project
    """
    # Create new project
    new_project = Project(
        title=project_data.title,
        description=project_data.description,
        total_amount=project_data.total_amount,
        currency=project_data.currency,
        completion_criteria=project_data.completion_criteria,
        due_date=project_data.due_date,
        start_date=project_data.start_date,
        creator_id=current_user.id,
        buyer_id=project_data.buyer_id,
        seller_id=project_data.seller_id,
        status=ProjectStatus.DRAFT,
    )

    db.add(new_project)
    await db.commit()
    await db.refresh(new_project)

    logger.info(f"Project created: {new_project.id} by user {current_user.email}")

    return ProjectResponse.model_validate(new_project)


@router.get("", response_model=ProjectListResponse)
async def list_projects(
    status_filter: Optional[ProjectStatus] = Query(None, description="Filter by project status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List projects for the current user.

    Args:
        status_filter: Optional status filter
        page: Page number
        page_size: Items per page
        current_user: Currently authenticated user
        db: Database session

    Returns:
        Paginated list of projects
    """
    # Build query - show projects where user is creator, buyer, or seller
    query = select(Project).where(
        (Project.creator_id == current_user.id)
        | (Project.buyer_id == current_user.id)
        | (Project.seller_id == current_user.id)
    )

    # Apply status filter if provided
    if status_filter:
        query = query.where(Project.status == status_filter)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Apply pagination
    query = query.offset((page - 1) * page_size).limit(page_size + 1)

    # Execute query
    result = await db.execute(query)
    projects = result.scalars().all()

    # Check if there are more items
    has_more = len(projects) > page_size
    items = projects[:page_size]

    return ProjectListResponse(
        items=[ProjectResponse.model_validate(p) for p in items],
        total=total,
        page=page,
        page_size=page_size,
        has_more=has_more,
    )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific project by ID.

    Args:
        project_id: Project UUID
        current_user: Currently authenticated user
        db: Database session

    Returns:
        Project details

    Raises:
        HTTPException: If project not found or user not authorized
    """
    # Fetch project
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    # Check if user has access
    if (
        project.creator_id != current_user.id
        and project.buyer_id != current_user.id
        and project.seller_id != current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="You don't have access to this project"
        )

    return ProjectResponse.model_validate(project)


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: UUID,
    project_update: ProjectUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update a project.

    Args:
        project_id: Project UUID
        project_update: Updated project data
        current_user: Currently authenticated user
        db: Database session

    Returns:
        Updated project

    Raises:
        HTTPException: If project not found or user not authorized
    """
    # Fetch project
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    # Only creator can update project
    if project.creator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Only the project creator can update it"
        )

    # Update fields
    if project_update.title is not None:
        project.title = project_update.title
    if project_update.description is not None:
        project.description = project_update.description
    if project_update.total_amount is not None:
        project.total_amount = project_update.total_amount
    if project_update.currency is not None:
        project.currency = project_update.currency
    if project_update.completion_criteria is not None:
        project.completion_criteria = project_update.completion_criteria
    if project_update.due_date is not None:
        project.due_date = project_update.due_date
    if project_update.status is not None:
        project.status = project_update.status

    await db.commit()
    await db.refresh(project)

    logger.info(f"Project updated: {project_id} by user {current_user.email}")

    return ProjectResponse.model_validate(project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a project (only if in draft status).

    Args:
        project_id: Project UUID
        current_user: Currently authenticated user
        db: Database session

    Raises:
        HTTPException: If project not found, user not authorized, or project not in draft
    """
    # Fetch project
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    # Only creator can delete project
    if project.creator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Only the project creator can delete it"
        )

    # Only allow deletion of draft projects
    if project.status != ProjectStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Only draft projects can be deleted"
        )

    await db.delete(project)
    await db.commit()

    logger.info(f"Project deleted: {project_id} by user {current_user.email}")
