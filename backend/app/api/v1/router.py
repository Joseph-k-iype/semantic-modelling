"""
Main API Router - aggregates all endpoint routers
"""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    users,
    workspaces,
    folders,
    models,
    diagrams,
    layouts,
    validation,
    lineage,
    export,
)

# Create main API router
api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"],
)

api_router.include_router(
    users.router,
    prefix="/users",
    tags=["Users"],
)

api_router.include_router(
    workspaces.router,
    prefix="/workspaces",
    tags=["Workspaces"],
)

api_router.include_router(
    folders.router,
    prefix="/folders",
    tags=["Folders"],
)

api_router.include_router(
    models.router,
    prefix="/models",
    tags=["Models"],
)

api_router.include_router(
    diagrams.router,
    prefix="/diagrams",
    tags=["Diagrams"],
)

api_router.include_router(
    layouts.router,
    prefix="/layouts",
    tags=["Layouts"],
)

api_router.include_router(
    validation.router,
    prefix="/validation",
    tags=["Validation"],
)

api_router.include_router(
    lineage.router,
    prefix="/lineage",
    tags=["Lineage"],
)

api_router.include_router(
    export.router,
    prefix="/export",
    tags=["Export"],
)