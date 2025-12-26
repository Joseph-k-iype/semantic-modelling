"""
Logging middleware for request/response logging

This middleware logs all incoming requests and outgoing responses with
structured logging, request IDs, and performance metrics.
"""

import time
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

logger = structlog.get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all incoming requests and outgoing responses
    
    This middleware:
    1. Generates a unique request ID for tracking
    2. Logs incoming request details (method, path, client info)
    3. Measures request processing time
    4. Logs response details (status code, duration)
    5. Adds request ID to response headers
    """
    
    # Paths to exclude from detailed logging (to reduce noise)
    EXCLUDE_PATHS = [
        "/health",
        "/ready",
    ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Log request and response details
        
        Args:
            request: FastAPI request object
            call_next: Next middleware or route handler
            
        Returns:
            Response from route handler
        """
        # Generate unique request ID for tracking
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Start timer for measuring request duration
        start_time = time.time()
        
        # Check if this path should be logged in detail
        should_log_detail = request.url.path not in self.EXCLUDE_PATHS
        
        # Extract request information
        method = request.method
        path = request.url.path
        query_params = dict(request.query_params) if request.query_params else {}
        client_host = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Log incoming request
        if should_log_detail:
            logger.info(
                "Incoming request",
                request_id=request_id,
                method=method,
                path=path,
                query_params=query_params if query_params else None,
                client_host=client_host,
                user_agent=user_agent,
                content_type=request.headers.get("content-type"),
                content_length=request.headers.get("content-length"),
            )
        else:
            # Just log basic info for health checks
            logger.debug(
                "Health check request",
                request_id=request_id,
                method=method,
                path=path,
            )
        
        # Initialize response variable
        response = None
        error_occurred = False
        
        try:
            # Process request through the rest of the middleware chain
            response = await call_next(request)
            
        except Exception as e:
            # If an error occurs, still log it
            error_occurred = True
            duration = time.time() - start_time
            
            logger.error(
                "Request failed with exception",
                request_id=request_id,
                method=method,
                path=path,
                duration_ms=round(duration * 1000, 2),
                error=str(e),
                error_type=type(e).__name__,
            )
            
            # Re-raise the exception to be handled by ErrorHandlerMiddleware
            raise
        
        finally:
            # Calculate request duration
            duration = time.time() - start_time
            
            # Log response if no error occurred
            if response is not None and not error_occurred:
                status_code = response.status_code
                
                # Determine log level based on status code
                if status_code >= 500:
                    log_level = logger.error
                elif status_code >= 400:
                    log_level = logger.warning
                else:
                    log_level = logger.info if should_log_detail else logger.debug
                
                # Log response
                log_level(
                    "Request completed",
                    request_id=request_id,
                    method=method,
                    path=path,
                    status_code=status_code,
                    duration_ms=round(duration * 1000, 2),
                    response_size=response.headers.get("content-length"),
                )
                
                # Add request ID to response headers for client tracking
                response.headers["X-Request-ID"] = request_id
                
                # Add timing information to response headers
                response.headers["X-Response-Time"] = f"{round(duration * 1000, 2)}ms"
                
                # Log slow requests (> 1 second)
                if duration > 1.0:
                    logger.warning(
                        "Slow request detected",
                        request_id=request_id,
                        method=method,
                        path=path,
                        duration_ms=round(duration * 1000, 2),
                        status_code=status_code,
                    )
        
        return response


class RequestLoggingContext:
    """
    Context manager for additional request logging
    
    Can be used in route handlers to add custom logging:
    
    ```python
    from app.middleware.logging_middleware import RequestLoggingContext
    
    @router.get("/example")
    async def example(request: Request):
        with RequestLoggingContext(request, "Processing example"):
            # Your code here
            pass
    ```
    """
    
    def __init__(self, request: Request, operation: str):
        """
        Initialize logging context
        
        Args:
            request: FastAPI request object
            operation: Description of the operation being performed
        """
        self.request = request
        self.operation = operation
        self.start_time = None
        self.logger = structlog.get_logger(__name__)
    
    def __enter__(self):
        """Start timing the operation"""
        self.start_time = time.time()
        self.logger.debug(
            f"Starting: {self.operation}",
            request_id=getattr(self.request.state, "request_id", None),
        )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Log operation completion"""
        duration = time.time() - self.start_time
        
        if exc_type is None:
            self.logger.debug(
                f"Completed: {self.operation}",
                request_id=getattr(self.request.state, "request_id", None),
                duration_ms=round(duration * 1000, 2),
            )
        else:
            self.logger.error(
                f"Failed: {self.operation}",
                request_id=getattr(self.request.state, "request_id", None),
                duration_ms=round(duration * 1000, 2),
                error=str(exc_val),
                error_type=exc_type.__name__ if exc_type else None,
            )
        
        # Don't suppress the exception
        return False