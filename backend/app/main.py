# backend/app/main.py
"""
FastAPI main application entry point - FIXED
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import structlog

from app.core.config import settings
from app.api.v1.router import api_router
from app.middleware.auth_middleware import AuthMiddleware
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

# Add CORS middleware - MUST be added FIRST before other middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Response-Time", "X-Total-Count"],
    max_age=3600,
)

# GZip compression
app.add_middleware(
    GZipMiddleware,
    minimum_size=1000
)

# Custom middleware (in order of execution)
# Note: Middleware executes in reverse order of addition
app.add_middleware(ErrorHandlerMiddleware)
app.add_middleware(LoggingMiddleware)
# AuthMiddleware is intentionally NOT added here - it would block all requests
# Instead, we use Depends(get_current_user) in endpoints that need auth


# Root endpoints (outside of API versioning)
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Enterprise Modeling Platform API",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "api": f"{settings.API_V1_STR}",
        "docs": "/docs",
        "redoc": "/redoc",
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    # Test database connection
    db_status = "unknown"
    try:
        from app.db.session import engine
        from sqlalchemy import text
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        db_status = "disconnected"
    
    # Test FalkorDB connection
    falkordb_status = "unknown"
    try:
        from app.graph.client import get_graph_client
        graph_client = get_graph_client()
        falkordb_status = "connected" if graph_client.is_connected() else "disconnected"
    except Exception as e:
        logger.error(f"FalkorDB health check failed: {str(e)}")
        falkordb_status = "disconnected"
    
    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "services": {
            "api": "operational",
            "database": db_status,
            "falkordb": falkordb_status,
        }
    }


@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint for Kubernetes"""
    return {"status": "ready"}


# Include API router with version prefix
app.include_router(api_router, prefix=settings.API_V1_STR)

# Log all registered routes on startup
@app.on_event("startup")
async def log_routes():
    """Log all registered routes for debugging"""
    logger.info("📋 Registered routes:")
    for route in app.routes:
        if hasattr(route, "methods"):
            methods = ", ".join(route.methods)
            logger.info(f"  {methods:8} {route.path}")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True
    )