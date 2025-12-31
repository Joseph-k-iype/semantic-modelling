# backend/app/main.py
"""
FastAPI main application entry point - COMPLETE AND FIXED
Path: backend/app/main.py
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import structlog
from sqlalchemy import text

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
    
    # Test database connection (async)
    try:
        from app.db.session import engine
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("✅ PostgreSQL connected successfully")
    except Exception as e:
        logger.error(f"❌ PostgreSQL connection error: {str(e)}")
    
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
    
    # Close database connections
    try:
        from app.db.session import close_db, close_sync_db
        await close_db()
        close_sync_db()
        logger.info("✅ Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database: {str(e)}")
    
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
# CRITICAL: CORS MIDDLEWARE MUST BE FIRST - THIS IS THE FIX
# ============================================================================

# Get CORS origins from settings
cors_origins = settings.cors_origins_list

# For development, ensure localhost variations are included
if settings.is_development:
    dev_origins = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8000",
    ]
    # Merge and deduplicate
    cors_origins = list(set(cors_origins + dev_origins))

# Log CORS configuration
logger.info("=" * 80)
logger.info("🔐 CORS Configuration")
logger.info("=" * 80)
for origin in cors_origins:
    logger.info(f"  ✓ {origin}")
logger.info("=" * 80)

# CRITICAL FIX: Add CORS middleware FIRST with explicit configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,  # List of allowed origins
    allow_credentials=True,       # Allow cookies and auth headers
    allow_methods=["*"],          # Allow all HTTP methods
    allow_headers=["*"],          # Allow all headers
    expose_headers=[
        "Content-Length",
        "Content-Type",
        "X-Request-ID",
        "X-Response-Time",
        "X-Total-Count",
    ],
    max_age=3600,  # Cache preflight requests for 1 hour
)

logger.info("✅ CORS middleware configured")

# ============================================================================
# OTHER MIDDLEWARE (Order matters!)
# ============================================================================

# Gzip compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Logging middleware
app.add_middleware(LoggingMiddleware)

# Error handling middleware
app.add_middleware(ErrorHandlerMiddleware)

# Trusted host middleware (only in production)
if settings.is_production:
    allowed_hosts = settings.ALLOWED_HOSTS.split(",") if settings.ALLOWED_HOSTS != "*" else ["*"]
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)

# ============================================================================
# ROUTES
# ============================================================================

# Health check endpoint (before API router)
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
    }


@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint"""
    # Test database connection (async)
    try:
        from app.db.session import engine
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    return {
        "status": "ready" if db_status == "healthy" else "not ready",
        "database": db_status,
        "version": settings.VERSION,
    }


# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "docs": "/docs",
        "api": settings.API_V1_STR,
    }


# Exception handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Handle 404 errors"""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": f"The requested resource at {request.url.path} was not found",
            "path": str(request.url.path),
        },
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {str(exc)}", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred. Please try again later.",
        },
    )


# CORS preflight handler
@app.options("/{rest_of_path:path}")
async def preflight_handler(rest_of_path: str):
    """
    Handle CORS preflight requests
    This ensures OPTIONS requests work correctly
    """
    return JSONResponse(
        status_code=200,
        content={"message": "OK"},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )