"""
Error handling middleware

This middleware catches all unhandled exceptions and returns appropriate
HTTP error responses with proper logging and error details.
"""

import traceback
from typing import Callable, Dict, Any, Optional
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.exc import (
    SQLAlchemyError,
    IntegrityError,
    DataError,
    OperationalError,
    ProgrammingError,
)
from pydantic import ValidationError
import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    Middleware to catch and handle all unhandled exceptions
    
    This middleware:
    1. Catches all exceptions that aren't handled by route handlers
    2. Logs errors with full context and stack traces
    3. Returns appropriate HTTP status codes
    4. Provides detailed errors in development, generic in production
    5. Handles specific exception types (database, validation, etc.)
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Catch and handle exceptions
        
        Args:
            request: FastAPI request object
            call_next: Next middleware or route handler
            
        Returns:
            Response from handler or error response
        """
        try:
            # Process request normally
            response = await call_next(request)
            return response
            
        except HTTPException as e:
            # FastAPI HTTP exceptions - these are intentional errors
            # Log at warning level since they're expected
            logger.warning(
                "HTTP exception",
                request_id=getattr(request.state, "request_id", None),
                path=request.url.path,
                method=request.method,
                status_code=e.status_code,
                detail=e.detail,
            )
            # Re-raise to let FastAPI handle it
            raise
            
        except ValidationError as e:
            # Pydantic validation errors - bad request data
            logger.warning(
                "Validation error",
                request_id=getattr(request.state, "request_id", None),
                path=request.url.path,
                method=request.method,
                errors=e.errors(),
            )
            
            return JSONResponse(
                status_code=422,
                content={
                    "detail": "Validation error",
                    "errors": self._format_validation_errors(e.errors()),
                    "request_id": getattr(request.state, "request_id", None),
                },
            )
            
        except IntegrityError as e:
            # Database integrity constraint violations
            logger.error(
                "Database integrity error",
                request_id=getattr(request.state, "request_id", None),
                path=request.url.path,
                method=request.method,
                error=str(e.orig) if hasattr(e, 'orig') else str(e),
            )
            
            # Try to extract meaningful error message
            error_message = self._extract_integrity_error_message(e)
            
            return JSONResponse(
                status_code=409,
                content={
                    "detail": "Conflict",
                    "error": error_message,
                    "request_id": getattr(request.state, "request_id", None),
                },
            )
            
        except DataError as e:
            # Database data errors (invalid data type, etc.)
            logger.error(
                "Database data error",
                request_id=getattr(request.state, "request_id", None),
                path=request.url.path,
                method=request.method,
                error=str(e.orig) if hasattr(e, 'orig') else str(e),
            )
            
            return JSONResponse(
                status_code=400,
                content={
                    "detail": "Invalid data",
                    "error": "The provided data is invalid for the database operation",
                    "request_id": getattr(request.state, "request_id", None),
                },
            )
            
        except OperationalError as e:
            # Database operational errors (connection issues, etc.)
            logger.error(
                "Database operational error",
                request_id=getattr(request.state, "request_id", None),
                path=request.url.path,
                method=request.method,
                error=str(e.orig) if hasattr(e, 'orig') else str(e),
            )
            
            return JSONResponse(
                status_code=503,
                content={
                    "detail": "Service unavailable",
                    "error": "Database is temporarily unavailable",
                    "request_id": getattr(request.state, "request_id", None),
                },
            )
            
        except ProgrammingError as e:
            # Database programming errors (SQL syntax, etc.)
            logger.error(
                "Database programming error",
                request_id=getattr(request.state, "request_id", None),
                path=request.url.path,
                method=request.method,
                error=str(e.orig) if hasattr(e, 'orig') else str(e),
                traceback=traceback.format_exc(),
            )
            
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "Internal server error",
                    "error": "A database error occurred" if not settings.is_development else str(e),
                    "request_id": getattr(request.state, "request_id", None),
                },
            )
            
        except SQLAlchemyError as e:
            # Generic SQLAlchemy errors
            logger.error(
                "Database error",
                request_id=getattr(request.state, "request_id", None),
                path=request.url.path,
                method=request.method,
                error=str(e),
                traceback=traceback.format_exc(),
            )
            
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "Database error",
                    "error": str(e) if settings.is_development else "A database error occurred",
                    "request_id": getattr(request.state, "request_id", None),
                },
            )
            
        except ValueError as e:
            # Value errors - bad input data
            logger.warning(
                "Value error",
                request_id=getattr(request.state, "request_id", None),
                path=request.url.path,
                method=request.method,
                error=str(e),
            )
            
            return JSONResponse(
                status_code=400,
                content={
                    "detail": "Bad request",
                    "error": str(e),
                    "request_id": getattr(request.state, "request_id", None),
                },
            )
            
        except PermissionError as e:
            # Permission errors
            logger.warning(
                "Permission denied",
                request_id=getattr(request.state, "request_id", None),
                path=request.url.path,
                method=request.method,
                user_id=getattr(request.state, "user_id", None),
                error=str(e),
            )
            
            return JSONResponse(
                status_code=403,
                content={
                    "detail": "Forbidden",
                    "error": "You don't have permission to perform this action",
                    "request_id": getattr(request.state, "request_id", None),
                },
            )
            
        except FileNotFoundError as e:
            # File not found errors
            logger.warning(
                "File not found",
                request_id=getattr(request.state, "request_id", None),
                path=request.url.path,
                method=request.method,
                error=str(e),
            )
            
            return JSONResponse(
                status_code=404,
                content={
                    "detail": "Not found",
                    "error": str(e),
                    "request_id": getattr(request.state, "request_id", None),
                },
            )
            
        except Exception as e:
            # Catch all other unhandled exceptions
            logger.error(
                "Unhandled exception",
                request_id=getattr(request.state, "request_id", None),
                path=request.url.path,
                method=request.method,
                error=str(e),
                error_type=type(e).__name__,
                traceback=traceback.format_exc(),
            )
            
            # Return detailed error in development, generic in production
            if settings.is_development:
                return JSONResponse(
                    status_code=500,
                    content={
                        "detail": "Internal server error",
                        "error": str(e),
                        "type": type(e).__name__,
                        "traceback": traceback.format_exc().split("\n"),
                        "request_id": getattr(request.state, "request_id", None),
                    },
                )
            else:
                return JSONResponse(
                    status_code=500,
                    content={
                        "detail": "Internal server error",
                        "error": "An unexpected error occurred",
                        "request_id": getattr(request.state, "request_id", None),
                    },
                )
    
    def _format_validation_errors(self, errors: list) -> list:
        """
        Format Pydantic validation errors for better readability
        
        Args:
            errors: List of Pydantic validation errors
            
        Returns:
            Formatted error list
        """
        formatted_errors = []
        for error in errors:
            formatted_errors.append({
                "field": " -> ".join(str(loc) for loc in error.get("loc", [])),
                "message": error.get("msg", ""),
                "type": error.get("type", ""),
            })
        return formatted_errors
    
    def _extract_integrity_error_message(self, error: IntegrityError) -> str:
        """
        Extract a user-friendly message from IntegrityError
        
        Args:
            error: SQLAlchemy IntegrityError
            
        Returns:
            User-friendly error message
        """
        error_str = str(error.orig) if hasattr(error, 'orig') else str(error)
        error_lower = error_str.lower()
        
        # Check for common constraint violations
        if "unique constraint" in error_lower or "duplicate key" in error_lower:
            # Try to extract field name
            if "email" in error_lower:
                return "An account with this email already exists"
            elif "name" in error_lower:
                return "An item with this name already exists"
            else:
                return "This value already exists and must be unique"
        
        elif "foreign key constraint" in error_lower:
            return "Referenced item does not exist"
        
        elif "not null constraint" in error_lower:
            return "Required field is missing"
        
        elif "check constraint" in error_lower:
            return "Value does not meet required constraints"
        
        # Default message
        return "Database constraint violation"


def get_error_response(
    status_code: int,
    detail: str,
    error: Optional[str] = None,
    request_id: Optional[str] = None,
) -> JSONResponse:
    """
    Helper function to create consistent error responses
    
    Args:
        status_code: HTTP status code
        detail: High-level error description
        error: Detailed error message (optional)
        request_id: Request ID for tracking (optional)
        
    Returns:
        JSONResponse with error details
    """
    content: Dict[str, Any] = {
        "detail": detail,
    }
    
    if error:
        content["error"] = error
    
    if request_id:
        content["request_id"] = request_id
    
    return JSONResponse(
        status_code=status_code,
        content=content,
    )