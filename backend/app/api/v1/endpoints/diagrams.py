"""
Diagram management endpoints
"""
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog
import uuid
from datetime import datetime

from app.db.session import get_db
from app.models.diagram import Diagram
from app.schemas.diagram import DiagramCreate, DiagramUpdate, DiagramResponse

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.get("/", response_model=List[DiagramResponse])
async def list_diagrams(
    workspace_id: str = Query(None, description="Filter by workspace"),
    model_id: str = Query(None, description="Filter by model"),
    diagram_type: str = Query(None, description="Filter by diagram type"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List diagrams with optional filters"""
    query = select(Diagram).where(Diagram.deleted_at.is_(None))
    
    if workspace_id:
        query = query.where(Diagram.workspace_id == workspace_id)
    
    if model_id:
        query = query.where(Diagram.model_id == model_id)
    
    if diagram_type:
        query = query.where(Diagram.type == diagram_type)
    
    query = query.offset(skip).limit(limit).order_by(Diagram.updated_at.desc())
    
    result = await db.execute(query)
    diagrams = result.scalars().all()
    
    logger.info("Diagrams listed", count=len(diagrams))
    
    return diagrams


@router.post("/", response_model=DiagramResponse, status_code=status.HTTP_201_CREATED)
async def create_diagram(
    diagram_in: DiagramCreate,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Create new diagram"""
    # Mock user ID - replace with actual authenticated user
    mock_user_id = str(uuid.uuid4())
    
    diagram = Diagram(
        name=diagram_in.name,
        description=diagram_in.description,
        type=diagram_in.type.value,
        workspace_id=str(diagram_in.workspace_id),
        model_id=str(diagram_in.model_id) if diagram_in.model_id else None,
        folder_id=str(diagram_in.folder_id) if diagram_in.folder_id else None,
        nodes=diagram_in.nodes or [],
        edges=diagram_in.edges or [],
        viewport=diagram_in.viewport or {"x": 0, "y": 0, "zoom": 1},
        metadata=diagram_in.metadata or {},
        created_by=mock_user_id,
        updated_by=mock_user_id,
    )
    
    db.add(diagram)
    await db.commit()
    await db.refresh(diagram)
    
    logger.info("Diagram created", diagram_id=str(diagram.id), name=diagram.name)
    
    return diagram


@router.get("/{diagram_id}", response_model=DiagramResponse)
async def get_diagram(
    diagram_id: str,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get diagram by ID"""
    result = await db.execute(
        select(Diagram).where(
            Diagram.id == diagram_id,
            Diagram.deleted_at.is_(None)
        )
    )
    diagram = result.scalar_one_or_none()
    
    if not diagram:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diagram not found"
        )
    
    logger.info("Diagram retrieved", diagram_id=diagram_id)
    
    return diagram


@router.put("/{diagram_id}", response_model=DiagramResponse)
async def update_diagram(
    diagram_id: str,
    diagram_in: DiagramUpdate,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Update diagram"""
    result = await db.execute(
        select(Diagram).where(
            Diagram.id == diagram_id,
            Diagram.deleted_at.is_(None)
        )
    )
    diagram = result.scalar_one_or_none()
    
    if not diagram:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diagram not found"
        )
    
    update_data = diagram_in.model_dump(exclude_unset=True)
    
    # Handle optional fields
    if "model_id" in update_data:
        model_id = update_data.pop("model_id")
        diagram.model_id = str(model_id) if model_id else None
    
    if "folder_id" in update_data:
        folder_id = update_data.pop("folder_id")
        diagram.folder_id = str(folder_id) if folder_id else None
    
    for field, value in update_data.items():
        setattr(diagram, field, value)
    
    # Mock user ID for updated_by
    diagram.updated_by = str(uuid.uuid4())
    diagram.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(diagram)
    
    logger.info("Diagram updated", diagram_id=diagram_id)
    
    return diagram


@router.delete("/{diagram_id}")
async def delete_diagram(
    diagram_id: str,
    hard_delete: bool = Query(False, description="Permanent delete"),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Delete diagram (soft delete by default)"""
    result = await db.execute(
        select(Diagram).where(Diagram.id == diagram_id)
    )
    diagram = result.scalar_one_or_none()
    
    if not diagram:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diagram not found"
        )
    
    if hard_delete:
        # Permanent deletion
        await db.delete(diagram)
        logger.info("Diagram permanently deleted", diagram_id=diagram_id)
    else:
        # Soft deletion
        diagram.deleted_at = datetime.utcnow()
        logger.info("Diagram soft deleted", diagram_id=diagram_id)
    
    await db.commit()
    
    return {"message": f"Diagram {diagram_id} deleted successfully"}


@router.post("/{diagram_id}/restore")
async def restore_diagram(
    diagram_id: str,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Restore a soft-deleted diagram"""
    result = await db.execute(
        select(Diagram).where(Diagram.id == diagram_id)
    )
    diagram = result.scalar_one_or_none()
    
    if not diagram:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diagram not found"
        )
    
    if diagram.deleted_at is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Diagram is not deleted"
        )
    
    diagram.deleted_at = None
    await db.commit()
    await db.refresh(diagram)
    
    logger.info("Diagram restored", diagram_id=diagram_id)
    
    return diagram