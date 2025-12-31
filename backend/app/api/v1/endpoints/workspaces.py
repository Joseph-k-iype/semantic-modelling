# backend/app/api/v1/endpoints/workspaces.py
"""
Workspace management endpoints - FIXED for ENUM type
Path: backend/app/api/v1/endpoints/workspaces.py
"""
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog
import uuid

from app.db.session import get_db
from app.models.workspace import Workspace, WorkspaceType
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
    """
    Create new workspace
    
    FIXED: Properly handles WorkspaceType enum
    """
    # Mock user ID - replace with actual authenticated user
    mock_user_id = uuid.uuid4()
    
    # CRITICAL FIX: Convert string to WorkspaceType enum
    workspace_type = workspace_in.type
    if isinstance(workspace_type, str):
        workspace_type = WorkspaceType(workspace_type)
    
    workspace = Workspace(
        name=workspace_in.name,
        description=workspace_in.description,
        type=workspace_type,  # Now properly a WorkspaceType enum
        created_by=mock_user_id,
        settings={},
        is_active=True,
    )
    
    db.add(workspace)
    
    try:
        await db.commit()
        await db.refresh(workspace)
        
        logger.info("Workspace created", workspace_id=str(workspace.id), name=workspace.name)
        
        return workspace
    except Exception as e:
        await db.rollback()
        logger.error("Failed to create workspace", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create workspace: {str(e)}"
        )


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get workspace by ID"""
    try:
        workspace_uuid = uuid.UUID(workspace_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid workspace ID format"
        )
    
    result = await db.execute(
        select(Workspace).where(Workspace.id == workspace_uuid)
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
    try:
        workspace_uuid = uuid.UUID(workspace_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid workspace ID format"
        )
    
    result = await db.execute(
        select(Workspace).where(Workspace.id == workspace_uuid)
    )
    workspace = result.scalar_one_or_none()
    
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found"
        )
    
    # Update fields
    update_data = workspace_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(workspace, field, value)
    
    try:
        await db.commit()
        await db.refresh(workspace)
        
        logger.info("Workspace updated", workspace_id=workspace_id)
        
        return workspace
    except Exception as e:
        await db.rollback()
        logger.error("Failed to update workspace", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update workspace: {str(e)}"
        )


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete workspace"""
    try:
        workspace_uuid = uuid.UUID(workspace_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid workspace ID format"
        )
    
    result = await db.execute(
        select(Workspace).where(Workspace.id == workspace_uuid)
    )
    workspace = result.scalar_one_or_none()
    
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found"
        )
    
    try:
        await db.delete(workspace)
        await db.commit()
        
        logger.info("Workspace deleted", workspace_id=workspace_id)
    except Exception as e:
        await db.rollback()
        logger.error("Failed to delete workspace", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete workspace: {str(e)}"
        )