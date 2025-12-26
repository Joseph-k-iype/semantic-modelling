"""
CORS middleware configuration

This module provides CORS (Cross-Origin Resource Sharing) configuration
for the FastAPI application. It uses FastAPI's built-in CORSMiddleware
but provides helper functions to configure it properly.
"""

from typing import List, Dict, Any
from app.core.config import settings


def get_cors_origins() -> List[str]:
    """
    Get allowed CORS origins from settings
    
    Returns:
        List of allowed origin URLs
    """
    return settings.cors_origins_list


def get_cors_config() -> Dict[str, Any]:
    """
    Get complete CORS configuration for FastAPI CORSMiddleware
    
    This configuration allows:
    - Requests from specified origins
    - All HTTP methods (GET, POST, PUT, DELETE, etc.)
    - All headers
    - Credentials (cookies, authorization headers)
    - Exposes custom headers to the client
    
    Returns:
        Dictionary with CORS configuration parameters
    """
    return {
        # Allowed origins (frontend URLs)
        "allow_origins": settings.cors_origins_list,
        
        # Allow credentials (cookies, authorization headers)
        "allow_credentials": True,
        
        # Allow all HTTP methods
        "allow_methods": ["*"],
        
        # Allow all headers
        "allow_headers": ["*"],
        
        # Expose these custom headers to the frontend
        "expose_headers": [
            "X-Request-ID",          # Request tracking ID
            "X-Response-Time",       # Request processing time
            "X-Total-Count",         # Total count for paginated responses
            "X-Page",                # Current page number
            "X-Per-Page",            # Items per page
            "X-Total-Pages",         # Total number of pages
        ],
        
        # Cache preflight requests for 1 hour
        "max_age": 3600,
    }


def is_cors_allowed(origin: str) -> bool:
    """
    Check if an origin is allowed for CORS requests
    
    Args:
        origin: Origin URL to check
        
    Returns:
        True if origin is allowed, False otherwise
    """
    allowed_origins = get_cors_origins()
    
    # Check for exact match
    if origin in allowed_origins:
        return True
    
    # Check for wildcard (*) - allow all origins
    if "*" in allowed_origins:
        return True
    
    # Check for pattern match (e.g., *.example.com)
    for allowed_origin in allowed_origins:
        if allowed_origin.startswith("*"):
            # Extract domain from wildcard pattern
            domain = allowed_origin.replace("*", "")
            if origin.endswith(domain):
                return True
    
    return False


def get_cors_headers(origin: str) -> Dict[str, str]:
    """
    Get CORS headers for a manual response
    
    This is useful when you need to add CORS headers manually
    (e.g., in custom middleware or error responses)
    
    Args:
        origin: Request origin
        
    Returns:
        Dictionary of CORS headers
    """
    headers = {}
    
    if is_cors_allowed(origin):
        headers["Access-Control-Allow-Origin"] = origin
        headers["Access-Control-Allow-Credentials"] = "true"
        headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, PATCH, OPTIONS"
        headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Request-ID"
        headers["Access-Control-Expose-Headers"] = "X-Request-ID, X-Response-Time, X-Total-Count"
        headers["Access-Control-Max-Age"] = "3600"
    
    return headers


# CORS configuration for development
DEV_CORS_CONFIG = {
    "allow_origins": [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8000",
    ],
    "allow_credentials": True,
    "allow_methods": ["*"],
    "allow_headers": ["*"],
    "expose_headers": ["X-Request-ID", "X-Response-Time"],
}


# CORS configuration for production
PROD_CORS_CONFIG = {
    "allow_origins": settings.cors_origins_list,
    "allow_credentials": True,
    "allow_methods": ["GET", "POST", "PUT", "DELETE", "PATCH"],
    "allow_headers": ["Content-Type", "Authorization", "X-Request-ID"],
    "expose_headers": ["X-Request-ID", "X-Response-Time", "X-Total-Count"],
    "max_age": 3600,
}


def get_environment_cors_config() -> Dict[str, Any]:
    """
    Get CORS configuration based on current environment
    
    Returns:
        CORS configuration for current environment
    """
    if settings.is_development:
        return DEV_CORS_CONFIG
    else:
        return PROD_CORS_CONFIG