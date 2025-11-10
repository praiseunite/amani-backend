"""
Authentication routes for user signup, login, and magic link authentication.
"""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from app.core.database import get_db
from app.core.auth import verify_password, get_password_hash, create_access_token
from app.core.supabase_client import send_magic_link
from app.core.dependencies import get_current_user, get_current_active_user
from app.core.config import settings
from app.models.user import User
from app.schemas.auth import (
    UserCreate,
    UserLogin,
    UserResponse,
    Token,
    MagicLinkRequest,
    MagicLinkResponse,
    PasswordChange,
    UserUpdate
)

router = APIRouter(prefix="/auth", tags=["authentication"])
logger = logging.getLogger(__name__)


@router.post("/signup", response_model=Token, status_code=status.HTTP_201_CREATED)
async def signup(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user with email and password.
    
    Args:
        user_data: User registration data
        db: Database session
        
    Returns:
        JWT token and user information
        
    Raises:
        HTTPException: If email already exists
    """
    # Check if user already exists
    result = await db.execute(
        select(User).where(User.email == user_data.email)
    )
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        phone_number=user_data.phone_number,
        role=user_data.role,
        hashed_password=hashed_password,
        is_active=True,
        is_verified=False,
        last_login=datetime.utcnow()
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": str(new_user.id),
            "email": new_user.email,
            "role": new_user.role.value
        },
        expires_delta=access_token_expires
    )
    
    logger.info(f"New user registered: {new_user.email}")
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.model_validate(new_user)
    )


@router.post("/login", response_model=Token)
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate user with email and password.
    
    Args:
        credentials: User login credentials
        db: Database session
        
    Returns:
        JWT token and user information
        
    Raises:
        HTTPException: If credentials are invalid
    """
    # Find user by email
    result = await db.execute(
        select(User).where(User.email == credentials.email)
    )
    user = result.scalar_one_or_none()
    
    if not user or not user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify password
    if not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    await db.commit()
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.value
        },
        expires_delta=access_token_expires
    )
    
    logger.info(f"User logged in: {user.email}")
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.model_validate(user)
    )


@router.post("/magic-link", response_model=MagicLinkResponse)
async def request_magic_link(
    request: MagicLinkRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Request a magic link for passwordless authentication.
    Uses Supabase Auth to send magic link email.
    
    Args:
        request: Magic link request with email
        db: Database session
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If magic link sending fails
    """
    try:
        # Check if user exists in our database
        result = await db.execute(
            select(User).where(User.email == request.email)
        )
        user = result.scalar_one_or_none()
        
        # If user doesn't exist, create a placeholder
        # The actual account will be created when they verify the magic link
        if not user:
            user = User(
                email=request.email,
                is_active=True,
                is_verified=False
            )
            db.add(user)
            await db.commit()
        
        # Send magic link via Supabase
        await send_magic_link(request.email)
        
        logger.info(f"Magic link requested for: {request.email}")
        
        return MagicLinkResponse(
            message="Magic link sent to your email. Please check your inbox.",
            email=request.email
        )
    
    except ValueError as e:
        # Supabase not configured
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Magic link authentication is not available. Please use email/password login."
        )
    except Exception as e:
        logger.error(f"Failed to send magic link: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send magic link. Please try again later."
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current authenticated user's information.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User information
    """
    return UserResponse.model_validate(current_user)


@router.put("/me", response_model=UserResponse)
async def update_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update current user's profile information.
    
    Args:
        user_update: Updated user information
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Updated user information
    """
    # Update user fields
    if user_update.full_name is not None:
        current_user.full_name = user_update.full_name
    if user_update.phone_number is not None:
        current_user.phone_number = user_update.phone_number
    if user_update.avatar_url is not None:
        current_user.avatar_url = user_update.avatar_url
    if user_update.bio is not None:
        current_user.bio = user_update.bio
    
    await db.commit()
    await db.refresh(current_user)
    
    logger.info(f"User profile updated: {current_user.email}")
    
    return UserResponse.model_validate(current_user)


@router.post("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    password_change: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Change user's password.
    
    Args:
        password_change: Current and new password
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If current password is incorrect
    """
    # Verify current password
    if not current_user.hashed_password or not verify_password(
        password_change.current_password,
        current_user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )
    
    # Update password
    current_user.hashed_password = get_password_hash(password_change.new_password)
    await db.commit()
    
    logger.info(f"Password changed for user: {current_user.email}")
    
    return {"message": "Password changed successfully"}
