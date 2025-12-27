"""
Model management endpoints
"""
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog
import uuid
from datetime import datetime

from app.db.session import get_db
from app.models.workspace import Model
from app.schemas.model import ModelCreate, ModelUpdate, ModelResponse

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.get("/", response_model=List[ModelResponse])
async def list_models(
    workspace_id: str = Query(None, description="Filter by workspace"),
    folder_id: str = Query(None, description="Filter by folder"),
    model_type: str = Query(None, description="Filter by model type"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List models with optional filters"""
    query = select(Model)
    
    if workspace_id:
        query = query.where(Model.workspace_id == workspace_id)
    
    if folder_id:
        query = query.where(Model.folder_id == folder_id)
    
    if model_type:
        query = query.where(Model.type == model_type)
    
    query = query.offset(skip).limit(limit).order_by(Model.updated_at.desc())
    
    result = await db.execute(query)
    models = result.scalars().all()
    
    logger.info("Models listed", count=len(models))
    
    return models


@router.post("/", response_model=ModelResponse, status_code=status.HTTP_201_CREATED)
async def create_model(
    model_in: ModelCreate,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Create new model"""
    # Mock user ID - replace with actual authenticated user
    mock_user_id = str(uuid.uuid4())
    
    model = Model(
        name=model_in.name,
        description=model_in.description,
        type=model_in.type.value if hasattr(model_in.type, 'value') else str(model_in.type),
        workspace_id=model_in.workspace_id,
        folder_id=model_in.folder_id if model_in.folder_id else None,
        meta_data=model_in.meta_data or {},
        created_by=mock_user_id,
        updated_by=mock_user_id,
    )
    
    db.add(model)
    await db.commit()
    await db.refresh(model)
    
    logger.info("Model created", model_id=str(model.id), name=model.name)
    
    return model


@router.get("/{model_id}", response_model=ModelResponse)
async def get_model(
    model_id: str,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get model by ID"""
    result = await db.execute(
        select(Model).where(Model.id == model_id)
    )
    model = result.scalar_one_or_none()
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )
    
    logger.info("Model retrieved", model_id=model_id)
    
    return model


@router.put("/{model_id}", response_model=ModelResponse)
async def update_model(
    model_id: str,
    model_in: ModelUpdate,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Update model"""
    result = await db.execute(
        select(Model).where(Model.id == model_id)
    )
    model = result.scalar_one_or_none()
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )
    
    update_data = model_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(model, field, value)
    
    # Mock user ID for updated_by
    model.updated_by = str(uuid.uuid4())
    model.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(model)
    
    logger.info("Model updated", model_id=model_id)
    
    return model


@router.delete("/{model_id}")
async def delete_model(
    model_id: str,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Delete model"""
    result = await db.execute(
        select(Model).where(Model.id == model_id)
    )
    model = result.scalar_one_or_none()
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )
    
    await db.delete(model)
    await db.commit()
    
    logger.info("Model deleted", model_id=model_id)
    
    return {"message": f"Model {model_id} deleted successfully"}