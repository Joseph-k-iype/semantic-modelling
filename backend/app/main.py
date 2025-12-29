# backend/app/main.py
"""
FastAPI main application entry point - CORS FIXED
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import structlog

from app.core.config import settings
from app.api.v1.router import api_router
from app.middleware.logging_middleware import LoggingMiddleware
from app.middleware.error_middleware import ErrorHandlerMiddleware

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup/shutdown events
    """
    # Startup
    logger.info("=" * 80)
    logger.info("🚀 Starting Enterprise Modeling Platform API")
    logger.info("=" * 80)
    logger.info(f"📍 Environment: {settings.ENVIRONMENT}")
    logger.info(f"🔧 Debug Mode: {settings.DEBUG}")
    logger.info(f"🌐 API Version: {settings.VERSION}")
    logger.info(f"📡 Host: {settings.HOST}:{settings.PORT}")
    logger.info(f"🔗 Database: {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}")
    logger.info(f"📊 FalkorDB: {settings.FALKORDB_HOST}:{settings.FALKORDB_PORT}")
    logger.info(f"⚡ Redis: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
    logger.info(f"🔐 CORS Origins: {', '.join(settings.cors_origins_list)}")
    logger.info("=" * 80)
    
    # Test FalkorDB connection
    try:
        from app.graph.client import get_graph_client
        graph_client = get_graph_client()
        if graph_client.is_connected():
            logger.info("✅ FalkorDB connected successfully")
        else:
            logger.warning("⚠️  FalkorDB connection failed - graph features will be disabled")
    except Exception as e:
        logger.error(f"❌ FalkorDB connection error: {str(e)}")
    
    logger.info("✅ Application startup complete\n")
    
    yield
    
    # Shutdown
    logger.info("\n" + "=" * 80)
    logger.info("🛑 Shutting down Enterprise Modeling Platform API")
    logger.info("=" * 80)
    
    # Close graph client
    try:
        from app.graph.client import close_graph_client
        close_graph_client()
        logger.info("✅ Graph client closed")
    except Exception as e:
        logger.error(f"Error closing graph client: {str(e)}")
    
    logger.info("✅ Application shutdown complete")
    logger.info("=" * 80)


# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Enterprise Modeling Platform - Visual Paradigm Alternative",
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    debug=settings.DEBUG,
)

# ============================================================================
# CRITICAL: CORS MIDDLEWARE MUST BE FIRST
# ============================================================================
# Get CORS origins - ensure they're properly formatted
cors_origins = settings.cors_origins_list

# Log CORS configuration for debugging
logger.info("Configuring CORS with origins:", origins=cors_origins)

# Add CORS middleware with explicit configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,  # List of allowed origins
    allow_credentials=True,       # Allow cookies and auth headers
    allow_methods=["*"],          # Allow all HTTP methods
    allow_headers=["*"],          # Allow all headers
    expose_headers=[              # Headers exposed to frontend
        "Content-Length",
        "Content-Type",
        "X-Request-ID",
        "X-Response-Time",
        "X-Total-Count",
    ],
    max_age=600,                  # Cache preflight requests for 10 minutes
)

# GZip compression for responses > 1000 bytes
app.add_middleware(
    GZipMiddleware,
    minimum_size=1000
)

# Custom middleware (executes in reverse order of addition)
app.add_middleware(ErrorHandlerMiddleware)
app.add_middleware(LoggingMiddleware)


# ============================================================================
# HEALTH CHECK ENDPOINTS (No Authentication Required)
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint - API information"""
    return {
        "message": "Enterprise Modeling Platform API",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "status": "operational",
        "endpoints": {
            "api": settings.API_V1_STR,
            "docs": "/docs",
            "redoc": "/redoc",
            "health": "/health",
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint - verify service is running"""
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
    }


@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint - verify all dependencies are ready"""
    checks = {
        "api": "ready",
        "database": "unknown",
        "graph": "unknown",
        "cache": "unknown",
    }
    
    # Check database connection
    try:
        from app.db.session import engine
        async with engine.begin() as conn:
            await conn.execute("SELECT 1")
        checks["database"] = "ready"
    except Exception as e:
        checks["database"] = f"error: {str(e)}"
    
    # Check graph database
    try:
        from app.graph.client import get_graph_client
        graph_client = get_graph_client()
        if graph_client.is_connected():
            checks["graph"] = "ready"
        else:
            checks["graph"] = "disconnected"
    except Exception as e:
        checks["graph"] = f"error: {str(e)}"
    
    # Determine overall status
    all_ready = all(status == "ready" for status in checks.values())
    
    return {
        "status": "ready" if all_ready else "degraded",
        "checks": checks,
    }


# ============================================================================
# API ROUTES
# ============================================================================

# Include API router with version prefix
app.include_router(api_router, prefix=settings.API_V1_STR)


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Custom 404 handler"""
    return {
        "error": "Not Found",
        "message": f"The requested endpoint {request.url.path} was not found",
        "status_code": 404,
    }


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Custom 500 handler"""
    logger.error("Internal server error", path=request.url.path, error=str(exc))
    return {
        "error": "Internal Server Error",
        "message": "An unexpected error occurred",
        "status_code": 500,
    }


# ============================================================================
# STARTUP MESSAGE
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )