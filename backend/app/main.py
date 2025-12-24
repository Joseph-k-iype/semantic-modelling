"""
Enterprise Modeling Platform - Backend API
Main application entry point
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.db.session import engine, init_db
from app.middleware.auth_middleware import AuthMiddleware
from app.middleware.logging_middleware import LoggingMiddleware
from app.middleware.error_middleware import ErrorHandlerMiddleware

# Initialize structured logger
logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Lifespan context manager for startup and shutdown events
    """
    # Startup
    logger.info("Starting Enterprise Modeling Platform API", version=settings.VERSION)
    
    try:
        # Initialize database
        await init_db()
        logger.info("Database initialized successfully")
        
        # Initialize graph database connection
        # Graph client initialization happens in dependencies
        logger.info("Graph database connection ready")
        
        # Initialize Redis connection
        # Redis client initialization happens in dependencies
        logger.info("Redis connection ready")
        
        logger.info("API startup complete", port=settings.PORT)
        
    except Exception as e:
        logger.error("Failed to start API", error=str(e))
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Enterprise Modeling Platform API")
    
    try:
        # Close database connections
        await engine.dispose()
        logger.info("Database connections closed")
        
        # Close Redis connections
        # Handled by dependency cleanup
        
        logger.info("API shutdown complete")
        
    except Exception as e:
        logger.error("Error during shutdown", error=str(e))


# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="""
    Enterprise Modeling Platform API
    
    An open-source, web-native, enterprise-grade modeling platform supporting:
    - ER Modeling, SQL, and Cypher
    - Full UML (all major diagram types)
    - Full BPMN 2.x
    - Graph-native lineage and impact analysis
    - Multi-workspace collaboration with governance
    - User-controlled, pluggable layout engines
    """,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan,
)


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# Add compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Add custom middleware
app.add_middleware(ErrorHandlerMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(AuthMiddleware)


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint for container orchestration
    """
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
    }


# Readiness check endpoint
@app.get("/ready", tags=["Health"])
async def readiness_check():
    """
    Readiness check endpoint - verifies all dependencies are available
    """
    from app.db.session import SessionLocal
    from app.cache.redis_client import get_redis_client
    from app.graph.client import get_graph_client
    
    checks = {
        "database": False,
        "redis": False,
        "graph_db": False,
    }
    
    try:
        # Check PostgreSQL
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        checks["database"] = True
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
    
    try:
        # Check Redis
        redis = get_redis_client()
        await redis.ping()
        checks["redis"] = True
    except Exception as e:
        logger.error("Redis health check failed", error=str(e))
    
    try:
        # Check FalkorDB
        graph = get_graph_client()
        graph.query("RETURN 1")
        checks["graph_db"] = True
    except Exception as e:
        logger.error("Graph DB health check failed", error=str(e))
    
    all_healthy = all(checks.values())
    status_code = 200 if all_healthy else 503
    
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "ready" if all_healthy else "not_ready",
            "checks": checks,
        }
    )


# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for unhandled exceptions
    """
    logger.exception(
        "Unhandled exception",
        path=request.url.path,
        method=request.method,
        error=str(exc),
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "type": "internal_error",
        },
    )


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint - API information
    """
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "description": "Enterprise Modeling Platform API",
        "documentation": f"{settings.API_V1_STR}/docs",
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )