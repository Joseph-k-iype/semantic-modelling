# backend/app/api/v1/endpoints/auth.py
"""
Authentication endpoints - COMPLETE FIX
Path: backend/app/api/v1/endpoints/auth.py

CRITICAL FIXES:
- Uses password_hash (matches database column)
- Uses UserRole enum properly
- Updates last_login_at on successful login
- Does NOT set created_by/updated_by during registration (trigger handles it)
- Proper error handling and logging
"""
from datetime import datetime, timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog

from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
    get_password_hash,
    decode_token,
)
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.auth import (
    Token,
    RefreshToken,
    UserRegister,
    UserLogin,
)
from app.schemas.user import UserResponse
from app.api.deps import get_current_user

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Register a new user
    
    CRITICAL FIXES:
    - Uses password_hash (not hashed_password)
    - Uses UserRole enum (not string)
    - Does NOT set created_by/updated_by (trigger handles it)
    - Creates personal workspace for new user
    
    Args:
        user_data: User registration data (email, password, optional username)
        db: Database session
        
    Returns:
        Created user data
        
    Raises:
        HTTPException: If email or username already exists
    """
    from app.models.workspace import Workspace, WorkspaceType
    
    try:
        # Check if user already exists by email
        result = await db.execute(
            select(User).where(User.email == user_data.email)
        )
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        
        # Check if username is provided and if it's already taken
        if user_data.username:
            result = await db.execute(
                select(User).where(User.username == user_data.username)
            )
            existing_username = result.scalar_one_or_none()
            
            if existing_username:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already taken",
                )
        
        # Generate username from email if not provided
        username = user_data.username if user_data.username else user_data.email.split('@')[0]
        
        # Create new user
        # CRITICAL: Do NOT set created_by or updated_by - trigger handles them
        user = User(
            email=user_data.email,
            username=username,
            password_hash=get_password_hash(user_data.password),  # ✅ FIXED
            full_name=user_data.full_name if user_data.full_name else username,
            role=UserRole.USER,  # ✅ FIXED: Use enum, not string
            is_active=True,
            is_verified=False
            # ✅ CRITICAL: Do NOT set created_by or updated_by
        )
        
        db.add(user)
        await db.flush()  # Flush to get user.id without committing
        
        # Create personal workspace for the user
        personal_workspace = Workspace(
            name=f"{username}'s Personal Workspace",
            slug=f"{username}-personal",
            type=WorkspaceType.PERSONAL,
            owner_id=user.id,
            is_active=True,
            created_by=user.id,  # Set explicitly for workspace
            updated_by=user.id   # Set explicitly for workspace
        )
        
        db.add(personal_workspace)
        await db.commit()
        await db.refresh(user)
        
        logger.info(
            "user_registered",
            user_id=str(user.id),
            email=user.email,
            username=user.username,
            workspace_created=True
        )
        
        return user
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error("registration_failed", error=str(e))
        import traceback
        traceback.print_exc()
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Please try again.",
        )


@router.post("/login", response_model=Token)
async def login(
    user_data: UserLogin,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    User login with email and password
    
    CRITICAL FIXES:
    - Uses password_hash (not hashed_password)
    - Updates last_login_at on successful login
    - Proper error handling
    
    Args:
        user_data: Login credentials (email, password)
        db: Database session
        
    Returns:
        JWT access and refresh tokens
        
    Raises:
        HTTPException: If credentials are invalid or user is inactive
    """
    try:
        # Find user by email
        result = await db.execute(
            select(User).where(User.email == user_data.email)
        )
        user = result.scalar_one_or_none()
        
        # Verify user exists and password is correct
        # CRITICAL: Use password_hash, not hashed_password
        if not user or not verify_password(user_data.password, user.password_hash):
            logger.warning(
                "login_failed",
                email=user_data.email,
                reason="invalid_credentials"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check if user is active
        if not user.is_active:
            logger.warning(
                "login_failed",
                email=user_data.email,
                user_id=str(user.id),
                reason="inactive_account"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive. Please contact support.",
            )
        
        # Update last login timestamp
        user.last_login_at = datetime.utcnow()
        await db.commit()
        
        # Create access token with user ID as subject
        access_token = create_access_token(
            subject=str(user.id),
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        
        # Create refresh token
        refresh_token = create_refresh_token(
            subject=str(user.id),
            expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        )
        
        logger.info(
            "user_logged_in",
            user_id=str(user.id),
            email=user.email,
            role=user.role.value
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error("login_failed", error=str(e))
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed. Please try again.",
        )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    token_data: RefreshToken,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Refresh access token using refresh token
    
    Args:
        token_data: Refresh token
        db: Database session
        
    Returns:
        New JWT access and refresh tokens
        
    Raises:
        HTTPException: If refresh token is invalid or expired
    """
    try:
        # Decode and validate refresh token
        payload = decode_token(token_data.refresh_token)
        user_id: str = payload.get("sub")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get user from database
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive",
            )
        
        # Create new tokens
        access_token = create_access_token(
            subject=str(user.id),
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        
        new_refresh_token = create_refresh_token(
            subject=str(user.id),
            expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        )
        
        logger.info(
            "token_refreshed",
            user_id=str(user.id),
            email=user.email
        )
        
        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("token_refresh_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get current user information
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User information
    """
    return current_user


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Logout current user
    
    Note: In a stateless JWT setup, logout is primarily client-side
    (removing tokens from storage). This endpoint is for logging purposes.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Success message
    """
    logger.info(
        "user_logged_out",
        user_id=str(current_user.id),
        email=current_user.email
    )
    
    return {"message": "Successfully logged out"}