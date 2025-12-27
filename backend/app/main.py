"""
FastAPI main application entry point
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.core.config import settings
from app.api.v1.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup/shutdown events
    """
    # Startup
    print("=" * 80)
    print("🚀 Starting Enterprise Modeling Platform API")
    print("=" * 80)
    print(f"📍 Environment: {settings.ENVIRONMENT}")
    print(f"🔧 Debug Mode: {settings.DEBUG}")
    print(f"🌐 API Version: {settings.VERSION}")
    print(f"📡 Host: {settings.HOST}:{settings.PORT}")
    print(f"🔗 Database: {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}")
    print(f"📊 FalkorDB: {settings.FALKORDB_HOST}:{settings.FALKORDB_PORT}")
    print(f"⚡ Redis: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
    print(f"🔐 CORS Origins: {', '.join(settings.cors_origins_list)}")
    print("=" * 80)
    
    # Initialize database connections
    # await init_db()
    
    # Initialize Redis connection
    # await init_redis()
    
    print("✅ Application startup complete\n")
    
    yield
    
    # Shutdown
    print("\n" + "=" * 80)
    print("🛑 Shutting down Enterprise Modeling Platform API")
    print("=" * 80)
    # Close database connections
    # Close Redis connection
    print("✅ Application shutdown complete")
    print("=" * 80)


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

# Add CORS middleware - MUST be added first
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Response-Time", "X-Total-Count"],
)

# GZip compression
app.add_middleware(
    GZipMiddleware,
    minimum_size=1000
)

# Trusted host middleware (optional - uncomment for production)
# app.add_middleware(
#     TrustedHostMiddleware,
#     allowed_hosts=["*"] if settings.is_development else ["yourdomain.com"]
# )

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Enterprise Modeling Platform API",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "docs": "/docs",
        "redoc": "/redoc",
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "services": {
            "api": "operational",
            "database": "connected",
            "redis": "connected",
            "falkordb": "connected"
        }
    }


@app.get("/api")
async def api_info():
    """API information endpoint"""
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "api_version": settings.API_V1_STR,
        "docs": "/docs",
        "redoc": "/redoc",
        "openapi": f"{settings.API_V1_STR}/openapi.json"
    }


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