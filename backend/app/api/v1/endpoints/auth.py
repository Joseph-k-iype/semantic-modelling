# backend/app/api/v1/endpoints/auth.py
"""
Authentication endpoints - FIXED with correct column names
Path: backend/app/api/v1/endpoints/auth.py
"""
from datetime import datetime, timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
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
from app.models.user import User
from app.schemas.auth import (
    Token,
    RefreshToken,
    UserRegister,
    UserLogin,
    PasswordReset,
    PasswordResetConfirm,
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
    """Register a new user"""
    # Check if user already exists
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
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    user = User(
        email=user_data.email,
        username=user_data.username if user_data.username else user_data.email.split('@')[0],
        hashed_password=hashed_password,
        full_name=user_data.full_name if user_data.full_name else user_data.email.split('@')[0],
        is_active=True,
        is_verified=False
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    logger.info("User registered", user_id=str(user.id), email=user.email)
    
    return user


@router.post("/login", response_model=Token)
async def login(
    user_data: UserLogin,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """User login with email and password - FIXED to update last_login_at"""
    # Find user by email
    result = await db.execute(
        select(User).where(User.email == user_data.email)
    )
    user = result.scalar_one_or_none()
    
    # Verify user exists and password is correct
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )
    
    # FIXED: Update last_login_at (not last_login)
    user.last_login_at = datetime.utcnow()
    await db.commit()
    
    # Create access and refresh tokens
    access_token = create_access_token(
        subject=str(user.id),
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    
    refresh_token = create_refresh_token(
        subject=str(user.id),
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    
    logger.info("User logged in", user_id=str(user.id), email=user.email)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_data: RefreshToken,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Refresh access token using refresh token"""
    try:
        # Decode refresh token
        payload = decode_token(refresh_data.refresh_token)
        user_id = payload.get("sub")
        token_type = payload.get("type")
        
        # Verify it's a refresh token
        if token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )
        
        # Get user from database
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
            )
        
        # Create new tokens
        access_token = create_access_token(
            subject=str(user.id),
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        )
        
        new_refresh_token = create_refresh_token(
            subject=str(user.id),
            expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )
        
        logger.info("Token refreshed", user_id=str(user.id))
        
        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
        }
        
    except Exception as e:
        logger.error("Token refresh failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Logout endpoint
    
    Note: Since we're using JWT tokens, actual logout happens client-side
    by deleting the tokens. This endpoint is here for API consistency
    and can be used for logging/analytics.
    """
    logger.info("User logged out", user_id=str(current_user.id), email=current_user.email)
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get current authenticated user information
    
    This endpoint requires authentication and returns the current user's profile.
    """
    logger.info("User info retrieved", user_id=str(current_user.id), email=current_user.email)
    return current_user


@router.post("/password-reset")
async def request_password_reset(
    reset_data: PasswordReset,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Request password reset (sends email with reset token)
    
    Note: Email functionality not implemented yet.
    This is a placeholder for future implementation.
    """
    # Find user by email
    result = await db.execute(
        select(User).where(User.email == reset_data.email)
    )
    user = result.scalar_one_or_none()
    
    # Don't reveal whether user exists or not (security)
    if not user:
        logger.warning("Password reset requested for non-existent email", email=reset_data.email)
        return {"message": "If the email exists, a password reset link will be sent"}
    
    # TODO: Generate reset token and send email
    logger.info("Password reset requested", user_id=str(user.id), email=user.email)
    
    return {"message": "If the email exists, a password reset link will be sent"}


@router.post("/password-reset/confirm")
async def confirm_password_reset(
    reset_data: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Confirm password reset with token
    
    Note: This is a placeholder for future implementation.
    """
    # TODO: Verify reset token and update password
    logger.info("Password reset confirmation attempted")
    
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Password reset not implemented yet",
    )