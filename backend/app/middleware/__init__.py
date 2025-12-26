"""
Middleware components for the application

This package contains all custom middleware for request processing:
- AuthMiddleware: JWT token validation
- LoggingMiddleware: Request/response logging
- ErrorHandlerMiddleware: Global exception handling
- CORS helpers: CORS configuration utilities
"""

from app.middleware.auth_middleware import AuthMiddleware
from app.middleware.logging_middleware import (
    LoggingMiddleware,
    RequestLoggingContext,
)
from app.middleware.error_middleware import (
    ErrorHandlerMiddleware,
    get_error_response,
)
from app.middleware.cors_middleware import (
    get_cors_config,
    get_cors_origins,
    get_cors_headers,
    is_cors_allowed,
    get_environment_cors_config,
    DEV_CORS_CONFIG,
    PROD_CORS_CONFIG,
)

__all__ = [
    # Middleware classes
    "AuthMiddleware",
    "LoggingMiddleware",
    "ErrorHandlerMiddleware",
    
    # Logging utilities
    "RequestLoggingContext",
    
    # Error utilities
    "get_error_response",
    
    # CORS utilities
    "get_cors_config",
    "get_cors_origins",
    "get_cors_headers",
    "is_cors_allowed",
    "get_environment_cors_config",
    
    # CORS configs
    "DEV_CORS_CONFIG",
    "PROD_CORS_CONFIG",
]