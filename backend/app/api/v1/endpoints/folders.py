"""
Folder management endpoints
"""
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog
import uuid
from datetime import datetime

from app.db.session import get_db
from app.models.workspace import Folder
from app.schemas.folder import FolderCreate, FolderUpdate, FolderResponse

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.get("/", response_model=List[FolderResponse])
async def list_folders(
    workspace_id: str = Query(..., description="Workspace ID to filter folders"),
    parent_id: str = Query(None, description="Parent folder ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List folders in a workspace"""
    query = select(Folder).where(Folder.workspace_id == workspace_id)
    
    if parent_id:
        query = query.where(Folder.parent_folder_id == parent_id)
    else:
        query = query.where(Folder.parent_folder_id.is_(None))
    
    query = query.offset(skip).limit(limit).order_by(Folder.created_at.desc())
    
    result = await db.execute(query)
    folders = result.scalars().all()
    
    logger.info("Folders listed", count=len(folders), workspace_id=workspace_id)
    
    return folders


@router.post("/", response_model=FolderResponse, status_code=status.HTTP_201_CREATED)
async def create_folder(
    folder_in: FolderCreate,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Create new folder"""
    # Mock user ID - replace with actual authenticated user
    mock_user_id = str(uuid.uuid4())
    
    folder = Folder(
        name=folder_in.name,
        description=folder_in.description,
        workspace_id=str(folder_in.workspace_id),
        parent_folder_id=str(folder_in.parent_id) if folder_in.parent_id else None,
        created_by=mock_user_id,
    )
    
    db.add(folder)
    await db.commit()
    await db.refresh(folder)
    
    logger.info("Folder created", folder_id=str(folder.id), name=folder.name)
    
    return folder


@router.get("/{folder_id}", response_model=FolderResponse)
async def get_folder(
    folder_id: str,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get folder by ID"""
    result = await db.execute(
        select(Folder).where(Folder.id == folder_id)
    )
    folder = result.scalar_one_or_none()
    
    if not folder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Folder not found"
        )
    
    logger.info("Folder retrieved", folder_id=folder_id)
    
    return folder


@router.put("/{folder_id}", response_model=FolderResponse)
async def update_folder(
    folder_id: str,
    folder_in: FolderUpdate,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Update folder"""
    result = await db.execute(
        select(Folder).where(Folder.id == folder_id)
    )
    folder = result.scalar_one_or_none()
    
    if not folder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Folder not found"
        )
    
    update_data = folder_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "parent_id" and value:
            setattr(folder, "parent_folder_id", str(value))
        elif field != "parent_id":
            setattr(folder, field, value)
    
    folder.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(folder)
    
    logger.info("Folder updated", folder_id=folder_id)
    
    return folder


@router.delete("/{folder_id}")
async def delete_folder(
    folder_id: str,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Delete folder"""
    result = await db.execute(
        select(Folder).where(Folder.id == folder_id)
    )
    folder = result.scalar_one_or_none()
    
    if not folder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Folder not found"
        )
    
    await db.delete(folder)
    await db.commit()
    
    logger.info("Folder deleted", folder_id=folder_id)
    
    return {"message": f"Folder {folder_id} deleted successfully"}