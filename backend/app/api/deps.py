# backend/app/api/deps.py
"""
FastAPI Dependencies - FIXED
Provides dependency injection for database sessions, authentication, and common utilities
"""
from typing import AsyncGenerator, Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import JWTError
import structlog

from app.core.config import settings
from app.core.security import decode_token
from app.db.session import get_db
from app.models.user import User

logger = structlog.get_logger(__name__)

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login",
    auto_error=False  # Don't auto-raise errors, handle manually
)


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
    token: Optional[str] = Depends(oauth2_scheme)
) -> User:
    """
    Dependency to get current authenticated user from JWT token
    
    Args:
        request: FastAPI request object
        db: Database session
        token: JWT token from Authorization header
        
    Returns:
        Current authenticated user
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # First check if user_id is already in request.state (set by AuthMiddleware)
    if hasattr(request.state, 'user_id') and request.state.user_id:
        user_id = request.state.user_id
    elif token:
        # Token provided but not validated by middleware yet
        try:
            payload = decode_token(token)
            user_id = payload.get("sub")
            token_type = payload.get("type")
            
            if not user_id or token_type != "access":
                raise credentials_exception
                
        except JWTError as e:
            logger.warning("Invalid token in get_current_user", error=str(e))
            raise credentials_exception
    else:
        # No token provided
        raise credentials_exception
    
    # Get user from database
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if user is None:
        logger.warning("User not found", user_id=user_id)
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependency to get current active user
    
    Args:
        current_user: Current user from get_current_user dependency
        
    Returns:
        Current active user
        
    Raises:
        HTTPException: If user is not active
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


async def get_current_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependency to get current superuser
    
    Args:
        current_user: Current user from get_current_user dependency
        
    Returns:
        Current superuser
        
    Raises:
        HTTPException: If user is not a superuser
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough privileges"
        )
    return current_user


async def get_optional_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
    token: Optional[str] = Depends(oauth2_scheme)
) -> Optional[User]:
    """
    Dependency to get current user if authenticated, None otherwise
    
    This is useful for endpoints that work differently based on authentication
    but don't require it.
    
    Args:
        request: FastAPI request object
        db: Database session
        token: JWT token from Authorization header
        
    Returns:
        Current user if authenticated, None otherwise
    """
    try:
        return await get_current_user(request, db, token)
    except HTTPException:
        return None