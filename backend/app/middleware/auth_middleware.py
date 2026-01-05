# backend/app/middleware/auth_middleware.py
"""
Authentication middleware for JWT token validation - FIXED
Path: backend/app/middleware/auth_middleware.py

CRITICAL FIX: Added /api/v1/diagrams/published to PUBLIC_ROUTES
"""

from typing import Callable, Optional
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from jose import JWTError
import structlog

from app.core.security import decode_token

logger = structlog.get_logger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware to validate JWT tokens on protected routes
    
    This middleware:
    1. Checks if the route requires authentication
    2. Extracts and validates JWT tokens from Authorization header
    3. Adds user information to request.state for use in endpoints
    4. Returns appropriate error responses for invalid/missing tokens
    """
    
    # Routes that don't require authentication
    PUBLIC_ROUTES = [
        "/",
        "/health",
        "/ready",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/v1/auth/login",
        "/api/v1/auth/login/oauth",
        "/api/v1/auth/register",
        "/api/v1/auth/refresh",
        "/api/v1/auth/password-reset",
        "/api/v1/auth/password-reset/confirm",
        "/api/v1/diagrams/published",  # CRITICAL FIX: Allow public access to published diagrams
    ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process each request and validate authentication if needed
        
        Args:
            request: FastAPI request object
            call_next: Next middleware or route handler
            
        Returns:
            Response from route handler or error response
        """
        # Check if route is public (doesn't require authentication)
        if self._is_public_route(request.url.path):
            return await call_next(request)
        
        # Get authorization header
        auth_header = request.headers.get("Authorization")
        
        if not auth_header:
            # No auth header - let endpoint decide if it's required
            # Some endpoints might be optionally authenticated
            return await call_next(request)
        
        # Validate token format (must be "Bearer <token>")
        if not auth_header.startswith("Bearer "):
            logger.warning(
                "Invalid authorization header format",
                path=request.url.path,
                method=request.method,
            )
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "detail": "Invalid authentication credentials",
                    "error": "Authorization header must start with 'Bearer'"
                },
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Extract token from header
        token = auth_header.replace("Bearer ", "")
        
        if not token:
            logger.warning(
                "Empty token in authorization header",
                path=request.url.path,
                method=request.method,
            )
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "detail": "Invalid authentication credentials",
                    "error": "Token cannot be empty"
                },
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        try:
            # Decode and validate token
            payload = decode_token(token)
            
            # Extract user information from token
            user_id = payload.get("sub")
            token_type = payload.get("type")
            
            if not user_id:
                logger.warning(
                    "Token missing user ID (sub claim)",
                    path=request.url.path,
                    method=request.method,
                )
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={
                        "detail": "Invalid token",
                        "error": "Token must contain user ID"
                    },
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Ensure it's an access token (not a refresh token)
            if token_type and token_type != "access":
                logger.warning(
                    "Wrong token type used",
                    path=request.url.path,
                    method=request.method,
                    token_type=token_type,
                )
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={
                        "detail": "Invalid token type",
                        "error": f"Expected access token, got {token_type}"
                    },
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Add user information to request state
            # This can be accessed in route handlers via request.state.user_id
            request.state.user_id = user_id
            request.state.token_type = token_type
            request.state.is_authenticated = True
            
            logger.debug(
                "Token validated successfully",
                user_id=user_id,
                path=request.url.path,
                method=request.method,
            )
            
        except JWTError as e:
            # Token is invalid, expired, or malformed
            logger.warning(
                "Invalid JWT token",
                path=request.url.path,
                method=request.method,
                error=str(e),
            )
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "detail": "Could not validate credentials",
                    "error": "Token is invalid or expired"
                },
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        except Exception as e:
            # Unexpected error during token validation
            logger.error(
                "Unexpected error during token validation",
                path=request.url.path,
                method=request.method,
                error=str(e),
                error_type=type(e).__name__,
            )
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "detail": "Authentication error",
                    "error": "An unexpected error occurred during authentication"
                },
            )
        
        # Continue processing request
        response = await call_next(request)
        return response
    
    def _is_public_route(self, path: str) -> bool:
        """
        Check if a route is public and doesn't require authentication
        
        Args:
            path: Request path to check
            
        Returns:
            True if route is public, False otherwise
        """
        # Exact match for public routes
        if path in self.PUBLIC_ROUTES:
            return True
        
        # Prefix match for documentation routes
        if path.startswith("/docs") or path.startswith("/redoc"):
            return True
        
        # OpenAPI schema is public
        if path.startswith("/openapi.json"):
            return True
        
        # Static files are public (if any)
        if path.startswith("/static"):
            return True
        
        return False