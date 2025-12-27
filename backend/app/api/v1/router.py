"""
API v1 Router
"""
from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    users,
    workspaces,
    folders,
    models,
    diagrams,
)

# Create API router
api_router = APIRouter()

# Include endpoint routers
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"]
)

api_router.include_router(
    users.router,
    prefix="/users",
    tags=["Users"]
)

api_router.include_router(
    workspaces.router,
    prefix="/workspaces",
    tags=["Workspaces"]
)

api_router.include_router(
    folders.router,
    prefix="/folders",
    tags=["Folders"]
)

api_router.include_router(
    models.router,
    prefix="/models",
    tags=["Models"]
)

api_router.include_router(
    diagrams.router,
    prefix="/diagrams",
    tags=["Diagrams"]
)


@api_router.get("/")
async def api_root():
    """API v1 root endpoint"""
    return {
        "message": "Enterprise Modeling Platform API v1",
        "endpoints": {
            "auth": "/api/v1/auth",
            "users": "/api/v1/users",
            "workspaces": "/api/v1/workspaces",
            "folders": "/api/v1/folders",
            "models": "/api/v1/models",
            "diagrams": "/api/v1/diagrams",
        }
    }