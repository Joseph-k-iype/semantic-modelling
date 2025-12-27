# backend/app/api/deps.py
"""
FastAPI Dependencies
Provides dependency injection for database sessions, authentication, and common utilities
"""
from typing import AsyncGenerator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
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
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    """
    Dependency to get current authenticated user from JWT token
    
    Args:
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
    
    # For now, return mock user for development
    # TODO: Implement real authentication
    from datetime import datetime
    import uuid
    
    # Mock user object
    class MockUser:
        def __init__(self):
            self.id = str(uuid.uuid4())
            self.email = "user@example.com"
            self.full_name = "Test User"
            self.is_active = True
            self.is_superuser = False
            self.created_at = datetime.utcnow()
            self.updated_at = datetime.utcnow()
    
    return MockUser()
    
    # Real implementation (uncomment when authentication is ready):
    """
    if not token:
        raise credentials_exception
    
    try:
        # Decode and validate token
        payload = decode_token(token)
        user_id: str = payload.get("sub")
        
        if user_id is None:
            raise credentials_exception
            
    except JWTError as e:
        logger.warning("Invalid token", error=str(e))
        raise credentials_exception
    
    # Get user from database
    from sqlalchemy import select
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
            detail="Inactive user"
        )
    
    return user
    """


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependency to get current active user
    
    Args:
        current_user: Current user from token
        
    Returns:
        Current active user
        
    Raises:
        HTTPException: If user is inactive
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
        current_user: Current user from token
        
    Returns:
        Current superuser
        
    Raises:
        HTTPException: If user is not a superuser
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


# Export all dependencies
__all__ = [
    "get_db",
    "get_current_user",
    "get_current_active_user",
    "get_current_superuser",
    "oauth2_scheme",
]