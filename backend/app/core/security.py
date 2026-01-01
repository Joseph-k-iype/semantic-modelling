# backend/app/core/security.py
"""
Security utilities for authentication and authorization
Path: backend/app/core/security.py

COMPLETE FIX:
- Direct bcrypt usage (no passlib dependency)
- Backward compatible password verification
- Proper JWT token creation and validation
- Clear error handling and logging
"""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from jose import JWTError, jwt
import bcrypt
import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash using bcrypt
    
    This function is backward compatible and works with:
    - Direct bcrypt hashes (current implementation)
    - Old passlib bcrypt hashes (fallback)
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password from database
        
    Returns:
        True if password matches, False otherwise
    """
    try:
        # Convert strings to bytes if needed
        if isinstance(plain_password, str):
            plain_password_bytes = plain_password.encode('utf-8')
        else:
            plain_password_bytes = plain_password
            
        if isinstance(hashed_password, str):
            hashed_password_bytes = hashed_password.encode('utf-8')
        else:
            hashed_password_bytes = hashed_password
        
        # Try direct bcrypt verification
        result = bcrypt.checkpw(plain_password_bytes, hashed_password_bytes)
        return result
        
    except ValueError as e:
        # If bcrypt fails with ValueError, the hash format might be invalid
        logger.warning(
            "password_verification_failed",
            error=str(e),
            hash_prefix=hashed_password[:10] if hashed_password else None
        )
        
        # Try passlib as fallback for old hashes
        try:
            from passlib.context import CryptContext
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            result = pwd_context.verify(plain_password, hashed_password)
            logger.info("password_verified_with_passlib_fallback")
            return result
        except Exception as fallback_error:
            logger.error(
                "passlib_fallback_failed",
                error=str(fallback_error)
            )
            return False
            
    except Exception as e:
        # Log unexpected errors but don't expose details to caller
        logger.error(
            "password_verification_error",
            error=str(e),
            error_type=type(e).__name__
        )
        return False


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt
    
    Args:
        password: Plain text password to hash
        
    Returns:
        Bcrypt hashed password as string
    """
    try:
        # Convert to bytes if needed
        if isinstance(password, str):
            password_bytes = password.encode('utf-8')
        else:
            password_bytes = password
        
        # Generate salt with 12 rounds (good balance of security and performance)
        salt = bcrypt.gensalt(rounds=12)
        
        # Hash the password
        hashed = bcrypt.hashpw(password_bytes, salt)
        
        # Return as string (bcrypt returns bytes)
        return hashed.decode('utf-8')
        
    except Exception as e:
        logger.error(
            "password_hashing_error",
            error=str(e),
            error_type=type(e).__name__
        )
        raise ValueError(f"Failed to hash password: {str(e)}")


def create_access_token(
    subject: str,
    expires_delta: Optional[timedelta] = None,
    additional_claims: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Create JWT access token
    
    Args:
        subject: User ID or identifier to include in token
        expires_delta: Token expiration time (default: from config)
        additional_claims: Optional additional claims to include
        
    Returns:
        Encoded JWT token string
    """
    try:
        # Calculate expiration time
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )
        
        # Build token payload
        to_encode = {
            "exp": expire,
            "iat": datetime.utcnow(),
            "sub": str(subject),
            "type": "access",
        }
        
        # Add any additional claims
        if additional_claims:
            to_encode.update(additional_claims)
        
        # Encode JWT
        encoded_jwt = jwt.encode(
            to_encode,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        
        return encoded_jwt
        
    except Exception as e:
        logger.error(
            "access_token_creation_error",
            error=str(e),
            subject=subject
        )
        raise ValueError(f"Failed to create access token: {str(e)}")


def create_refresh_token(
    subject: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create JWT refresh token
    
    Args:
        subject: User ID or identifier to include in token
        expires_delta: Token expiration time (default: from config)
        
    Returns:
        Encoded JWT refresh token string
    """
    try:
        # Calculate expiration time
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                days=settings.REFRESH_TOKEN_EXPIRE_DAYS
            )
        
        # Build token payload
        to_encode = {
            "exp": expire,
            "iat": datetime.utcnow(),
            "sub": str(subject),
            "type": "refresh",
        }
        
        # Encode JWT
        encoded_jwt = jwt.encode(
            to_encode,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        
        return encoded_jwt
        
    except Exception as e:
        logger.error(
            "refresh_token_creation_error",
            error=str(e),
            subject=subject
        )
        raise ValueError(f"Failed to create refresh token: {str(e)}")


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate JWT token
    
    Args:
        token: JWT token string to decode
        
    Returns:
        Decoded token payload
        
    Raises:
        JWTError: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
        
    except jwt.ExpiredSignatureError:
        logger.warning("token_expired")
        raise JWTError("Token has expired")
        
    except jwt.JWTClaimsError:
        logger.warning("token_invalid_claims")
        raise JWTError("Invalid token claims")
        
    except Exception as e:
        logger.error(
            "token_decode_error",
            error=str(e),
            error_type=type(e).__name__
        )
        raise JWTError(f"Could not validate credentials: {str(e)}")


def verify_token(token: str, token_type: str = "access") -> Optional[str]:
    """
    Verify token and extract subject (user ID)
    
    Args:
        token: JWT token to verify
        token_type: Expected token type ("access" or "refresh")
        
    Returns:
        Subject (user ID) from token, or None if invalid
    """
    try:
        payload = decode_token(token)
        
        # Verify token type
        if payload.get("type") != token_type:
            logger.warning(
                "token_type_mismatch",
                expected=token_type,
                actual=payload.get("type")
            )
            return None
        
        # Extract subject (user ID)
        subject: str = payload.get("sub")
        return subject
        
    except JWTError as e:
        logger.warning("token_verification_failed", error=str(e))
        return None
    except Exception as e:
        logger.error("token_verification_error", error=str(e))
        return None