"""
CRUD operations for User model.
Includes error handling and session management.
"""
from typing import Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.exc import IntegrityError

from app.models.user import User, UserRole
from app.core.exceptions import NotFoundError, ConflictError


async def create_user(
    db: AsyncSession,
    email: str,
    full_name: Optional[str] = None,
    hashed_password: Optional[str] = None,
    role: UserRole = UserRole.CLIENT,
    phone_number: Optional[str] = None,
    is_active: bool = True,
    is_verified: bool = False
) -> User:
    """
    Create a new user.
    
    Args:
        db: Database session
        email: User email (required)
        full_name: User full name
        hashed_password: Hashed password
        role: User role (default: CLIENT)
        phone_number: User phone number
        is_active: Whether user is active
        is_verified: Whether user email is verified
        
    Returns:
        Created user object
        
    Raises:
        ConflictError: If email already exists
    """
    try:
        new_user = User(
            email=email,
            full_name=full_name,
            hashed_password=hashed_password,
            role=role,
            phone_number=phone_number,
            is_active=is_active,
            is_verified=is_verified
        )
        
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        
        return new_user
    except IntegrityError as e:
        await db.rollback()
        if "unique constraint" in str(e.orig).lower() and "email" in str(e.orig).lower():
            raise ConflictError(f"User with email {email} already exists")
        raise ConflictError("User creation failed due to database constraint violation")


async def get_user_by_id(db: AsyncSession, user_id: UUID) -> User:
    """
    Get a user by ID.
    
    Args:
        db: Database session
        user_id: User UUID
        
    Returns:
        User object
        
    Raises:
        NotFoundError: If user not found
    """
    try:
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if user is None:
            raise NotFoundError(f"User with ID {user_id} not found")
        
        return user
    except Exception as e:
        if isinstance(e, NotFoundError):
            raise
        await db.rollback()
        raise


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """
    Get a user by email.
    
    Args:
        db: Database session
        email: User email
        
    Returns:
        User object or None if not found
    """
    try:
        result = await db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    except Exception:
        await db.rollback()
        raise


async def get_users(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    role: Optional[UserRole] = None,
    is_active: Optional[bool] = None
) -> List[User]:
    """
    Get a list of users with optional filtering.
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        role: Filter by user role
        is_active: Filter by active status
        
    Returns:
        List of user objects
    """
    try:
        query = select(User)
        
        if role is not None:
            query = query.where(User.role == role)
        
        if is_active is not None:
            query = query.where(User.is_active == is_active)
        
        query = query.offset(skip).limit(limit)
        
        result = await db.execute(query)
        return list(result.scalars().all())
    except Exception:
        await db.rollback()
        raise


async def update_user(
    db: AsyncSession,
    user_id: UUID,
    **kwargs
) -> User:
    """
    Update a user.
    
    Args:
        db: Database session
        user_id: User UUID
        **kwargs: Fields to update
        
    Returns:
        Updated user object
        
    Raises:
        NotFoundError: If user not found
        ConflictError: If update violates constraints
    """
    try:
        # Check if user exists
        user = await get_user_by_id(db, user_id)
        
        # Filter out None values and non-updatable fields
        update_data = {k: v for k, v in kwargs.items() if v is not None and k != 'id'}
        
        if not update_data:
            return user
        
        # Update user
        stmt = update(User).where(User.id == user_id).values(**update_data)
        await db.execute(stmt)
        await db.commit()
        await db.refresh(user)
        
        return user
    except IntegrityError as e:
        await db.rollback()
        if "unique constraint" in str(e.orig).lower():
            raise ConflictError("Update failed due to unique constraint violation")
        raise ConflictError("Update failed due to database constraint violation")
    except Exception as e:
        if isinstance(e, (NotFoundError, ConflictError)):
            raise
        await db.rollback()
        raise


async def delete_user(db: AsyncSession, user_id: UUID) -> bool:
    """
    Delete a user.
    
    Args:
        db: Database session
        user_id: User UUID
        
    Returns:
        True if deleted successfully
        
    Raises:
        NotFoundError: If user not found
    """
    try:
        # Check if user exists
        await get_user_by_id(db, user_id)
        
        # Delete user
        stmt = delete(User).where(User.id == user_id)
        result = await db.execute(stmt)
        await db.commit()
        
        return result.rowcount > 0
    except Exception as e:
        if isinstance(e, NotFoundError):
            raise
        await db.rollback()
        raise
