# backend/app/api/v1/endpoints/auth.py
"""
Authentication endpoints - COMPLETE FIX
Path: backend/app/api/v1/endpoints/auth.py

CRITICAL FIXES:
- Uses password_hash (matches database column)
- Uses UserRole enum properly
- Updates last_login_at on successful login
- Does NOT set created_by/updated_by during user registration (trigger handles it)
- REMOVED owner_id from Workspace creation (field doesn't exist in model)
- Uses created_by for workspace ownership tracking
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
    - REMOVED owner_id from Workspace (doesn't exist in model)
    - Uses created_by for workspace ownership
    
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
        # ✅ CRITICAL FIX: Removed owner_id (doesn't exist in Workspace model)
        # The workspace uses created_by as the owner field
        personal_workspace = Workspace(
            name=f"{username}'s Personal Workspace",
            slug=f"{username}-personal",
            type=WorkspaceType.PERSONAL,
            is_active=True,
            created_by=user.id,
            updated_by=user.id
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
            detail="Registration failed. Please try again."
        )


@router.post("/login", response_model=Token)
async def login(
    user_data: UserLogin,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Login user and return JWT tokens
    
    CRITICAL FIXES:
    - Uses password_hash (not hashed_password)
    - Updates last_login_at on successful login
    - Proper error messages for security
    
    Args:
        user_data: User login credentials (email, password)
        db: Database session
        
    Returns:
        Access and refresh JWT tokens
        
    Raises:
        HTTPException: If credentials are invalid or account is inactive
    """
    try:
        # Get user by email
        result = await db.execute(
            select(User).where(User.email == user_data.email)
        )
        user = result.scalar_one_or_none()
        
        # Verify user exists and password is correct
        if not user or not verify_password(user_data.password, user.password_hash):
            logger.warning(
                "login_failed",
                email=user_data.email,
                reason="invalid_credentials"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
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
        
        # Create access and refresh tokens
        access_token = create_access_token(subject=str(user.id))
        refresh_token = create_refresh_token(subject=str(user.id))
        
        logger.info(
            "user_logged_in",
            user_id=str(user.id),
            email=user.email
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("login_error", error=str(e))
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed. Please try again."
        )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_data: RefreshToken,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Refresh access token using refresh token
    
    Args:
        refresh_data: Refresh token
        db: Database session
        
    Returns:
        New access and refresh tokens
        
    Raises:
        HTTPException: If refresh token is invalid or user not found
    """
    try:
        # Decode and verify refresh token
        user_id = decode_token(refresh_data.refresh_token, token_type="refresh")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )
        
        # Get user from database
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive",
            )
        
        # Create new tokens
        access_token = create_access_token(subject=str(user.id))
        new_refresh_token = create_refresh_token(subject=str(user.id))
        
        logger.info(
            "token_refreshed",
            user_id=str(user.id)
        )
        
        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("token_refresh_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not refresh token",
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
        Current user data
    """
    logger.info(
        "user_info_retrieved",
        user_id=str(current_user.id)
    )
    
    return current_user


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Logout current user
    
    Note: In a stateless JWT implementation, logout is handled client-side
    by removing the tokens. This endpoint exists for logging purposes and
    future token blacklisting implementation.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Success message
    """
    logger.info(
        "user_logged_out",
        user_id=str(current_user.id)
    )
    
    return {"message": "Successfully logged out"}