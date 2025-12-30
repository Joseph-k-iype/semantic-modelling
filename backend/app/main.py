# backend/app/main.py
"""
FastAPI main application entry point - COMPLETE with FIXED CORS
Path: backend/app/main.py
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
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
# This ensures CORS headers are added to ALL responses, including errors
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
    # Merge with configured origins, removing duplicates
    cors_origins = list(set(cors_origins + dev_origins))

# Log CORS configuration
logger.info("=" * 80)
logger.info("🔐 CORS Configuration")
logger.info("=" * 80)
for origin in cors_origins:
    logger.info(f"  ✓ {origin}")
logger.info("=" * 80)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,       # List of allowed origins
    allow_credentials=True,           # Allow cookies and auth headers
    allow_methods=["*"],              # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],              # Allow all headers
    expose_headers=[                  # Headers that frontend can access
        "Content-Length",
        "Content-Type",
        "X-Request-ID",
        "X-Response-Time",
        "X-Total-Count",
    ],
    max_age=3600,                     # Cache preflight requests for 1 hour
)

# ============================================================================
# OTHER MIDDLEWARE (Order matters!)
# ============================================================================

# Trusted proxy configuration (if behind reverse proxy)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"] if settings.is_development else settings.ALLOWED_HOSTS.split(",")
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
        from sqlalchemy import text
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
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
    
    # Check Redis cache
    try:
        from app.cache.redis_client import get_redis_client
        redis_client = get_redis_client()
        await redis_client.ping()
        checks["cache"] = "ready"
    except Exception as e:
        checks["cache"] = f"error: {str(e)}"
    
    # Determine overall status
    all_ready = all(status == "ready" for status in checks.values())
    
    return {
        "status": "ready" if all_ready else "degraded",
        "checks": checks,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
    }


# ============================================================================
# INCLUDE API ROUTER
# ============================================================================

app.include_router(api_router, prefix=settings.API_V1_STR)


# ============================================================================
# STARTUP MESSAGE
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    logger.info("=" * 80)
    logger.info("🚀 Starting server with uvicorn")
    logger.info(f"📡 http://{settings.HOST}:{settings.PORT}")
    logger.info(f"📚 Docs: http://{settings.HOST}:{settings.PORT}/docs")
    logger.info("=" * 80)
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )