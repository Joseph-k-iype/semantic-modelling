"""
Workspace management endpoints
"""
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog
import uuid
from datetime import datetime

from app.db.session import get_db
from app.models.workspace import Workspace
from app.schemas.workspace import WorkspaceCreate, WorkspaceUpdate, WorkspaceResponse

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.get("/", response_model=List[WorkspaceResponse])
async def list_workspaces(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List all workspaces"""
    result = await db.execute(
        select(Workspace)
        .offset(skip)
        .limit(limit)
        .order_by(Workspace.created_at.desc())
    )
    workspaces = result.scalars().all()
    
    logger.info("Workspaces listed", count=len(workspaces))
    
    return workspaces


@router.post("/", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    workspace_in: WorkspaceCreate,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Create new workspace"""
    # Mock user ID - replace with actual authenticated user
    mock_user_id = str(uuid.uuid4())
    
    workspace = Workspace(
        name=workspace_in.name,
        description=workspace_in.description,
        type=workspace_in.type.value,
        created_by=mock_user_id,
    )
    
    db.add(workspace)
    await db.commit()
    await db.refresh(workspace)
    
    logger.info("Workspace created", workspace_id=str(workspace.id), name=workspace.name)
    
    return workspace


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get workspace by ID"""
    result = await db.execute(
        select(Workspace).where(Workspace.id == workspace_id)
    )
    workspace = result.scalar_one_or_none()
    
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found"
        )
    
    logger.info("Workspace retrieved", workspace_id=workspace_id)
    
    return workspace


@router.put("/{workspace_id}", response_model=WorkspaceResponse)
async def update_workspace(
    workspace_id: str,
    workspace_in: WorkspaceUpdate,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Update workspace"""
    result = await db.execute(
        select(Workspace).where(Workspace.id == workspace_id)
    )
    workspace = result.scalar_one_or_none()
    
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found"
        )
    
    update_data = workspace_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(workspace, field, value)
    
    workspace.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(workspace)
    
    logger.info("Workspace updated", workspace_id=workspace_id)
    
    return workspace


@router.delete("/{workspace_id}")
async def delete_workspace(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Delete workspace"""
    result = await db.execute(
        select(Workspace).where(Workspace.id == workspace_id)
    )
    workspace = result.scalar_one_or_none()
    
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found"
        )
    
    await db.delete(workspace)
    await db.commit()
    
    logger.info("Workspace deleted", workspace_id=workspace_id)
    
    return {"message": f"Workspace {workspace_id} deleted successfully"}