# backend/app/api/v1/endpoints/diagrams.py
"""
Diagram Management Endpoints - COMPLETE AND FIXED
Path: backend/app/api/v1/endpoints/diagrams.py
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime
import uuid
import asyncio
import structlog

from app.db.session import get_db
from app.models.diagram import Diagram
from app.models.model import Model, ModelType, ModelStatus
from app.models.workspace import Workspace, WorkspaceType
from app.models.user import User
from app.api.deps import get_current_user

logger = structlog.get_logger(__name__)
router = APIRouter()


# ============================================================================
# REQUEST/RESPONSE SCHEMAS
# ============================================================================

class DiagramCreateRequest(BaseModel):
    """Request schema for creating a diagram"""
    name: str
    notation_type: str  # Frontend uses notation_type
    description: Optional[str] = None
    model_id: Optional[str] = None
    model_name: Optional[str] = None
    workspace_id: Optional[str] = None


class DiagramUpdateRequest(BaseModel):
    """Request schema for updating a diagram"""
    name: Optional[str] = None
    description: Optional[str] = None
    notation_config: Optional[Dict[str, Any]] = None
    visible_concepts: Optional[List[str]] = None
    settings: Optional[Dict[str, Any]] = None


class DiagramResponse(BaseModel):
    """Response schema for diagram"""
    id: str
    name: str
    notation: str
    notation_type: str  # For frontend compatibility
    model_id: str
    description: Optional[str] = None
    notation_config: Dict[str, Any] = {}
    visible_concepts: List[str] = []
    settings: Dict[str, Any] = {}
    created_by: str
    updated_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def get_or_create_personal_workspace(
    db: AsyncSession,
    user: User
) -> Workspace:
    """Get user's personal workspace or create it"""
    result = await db.execute(
        select(Workspace).where(
            Workspace.created_by == user.id,
            Workspace.type == WorkspaceType.PERSONAL
        )
    )
    workspace = result.scalar_one_or_none()
    
    if workspace:
        logger.info("Found existing personal workspace", user_id=str(user.id), workspace_id=str(workspace.id))
        return workspace
    
    # Create personal workspace
    workspace = Workspace(
        name=f"{user.username}'s Workspace",
        description="Personal workspace",
        type=WorkspaceType.PERSONAL,
        created_by=user.id,
        settings={},
        is_active=True
    )
    db.add(workspace)
    await db.flush()
    
    logger.info("Created personal workspace", user_id=str(user.id), workspace_id=str(workspace.id))
    return workspace


def diagram_to_response(diagram: Diagram) -> DiagramResponse:
    """Convert diagram model to response schema"""
    return DiagramResponse(
        id=str(diagram.id),
        name=diagram.name,
        notation=diagram.notation,
        notation_type=diagram.notation,  # Frontend compatibility
        model_id=str(diagram.model_id),
        description=diagram.description,
        notation_config=diagram.notation_config or {},
        visible_concepts=[str(c) for c in (diagram.visible_concepts or [])],
        settings=diagram.settings or {},
        created_by=str(diagram.created_by),
        updated_by=str(diagram.updated_by) if diagram.updated_by else None,
        created_at=diagram.created_at,
        updated_at=diagram.updated_at
    )


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/", response_model=DiagramResponse, status_code=status.HTTP_201_CREATED)
async def create_diagram(
    diagram_data: DiagramCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new diagram (and model if needed)
    
    FIXED: Handles case where model already exists with the same name
    If model_id is not provided, creates a new model in the user's personal workspace.
    """
    try:
        # Get or create workspace
        if diagram_data.workspace_id:
            workspace_id = uuid.UUID(diagram_data.workspace_id)
        else:
            workspace = await get_or_create_personal_workspace(db, current_user)
            workspace_id = workspace.id
        
        # Get or create model
        if diagram_data.model_id:
            # Use existing model
            model_id = uuid.UUID(diagram_data.model_id)
            result = await db.execute(
                select(Model).where(Model.id == model_id)
            )
            model = result.scalar_one_or_none()
            
            if not model:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Model not found"
                )
            
            logger.info("Using existing model", model_id=str(model.id), model_name=model.name)
        else:
            # FIXED: Create model or reuse existing one with same name
            model_name = diagram_data.model_name or f"Model for {diagram_data.name}"
            
            # Check if model already exists
            result = await db.execute(
                select(Model).where(
                    Model.workspace_id == workspace_id,
                    Model.name == model_name
                )
            )
            model = result.scalar_one_or_none()
            
            if model:
                # Reuse existing model
                logger.info(
                    "Reusing existing model",
                    model_id=str(model.id),
                    model_name=model.name,
                    diagram_name=diagram_data.name
                )
            else:
                # Create new model
                model = Model(
                    workspace_id=workspace_id,
                    name=model_name,
                    description=f"Auto-generated model for diagram: {diagram_data.name}",
                    type=ModelType.ER,
                    status=ModelStatus.DRAFT,
                    created_by=current_user.id,
                    version=1,
                    tags=[],
                    metadata={}
                )
                db.add(model)
                await db.flush()
                await db.refresh(model)
                
                logger.info(
                    "Created new model",
                    model_id=str(model.id),
                    model_name=model.name,
                    diagram_name=diagram_data.name
                )
        
        # FIXED: Check if diagram name already exists for this model with retry logic for race conditions
        diagram_name = diagram_data.name
        counter = 1
        max_retries = 5
        retry_count = 0
        diagram = None
        
        while retry_count < max_retries:
            try:
                # Find a unique name
                while True:
                    result = await db.execute(
                        select(Diagram).where(
                            Diagram.model_id == model.id,
                            Diagram.name == diagram_name
                        )
                    )
                    existing_diagram = result.scalar_one_or_none()
                    
                    if not existing_diagram:
                        # Name is unique, we can use it
                        break
                    
                    # Name exists, try with a counter
                    diagram_name = f"{diagram_data.name} ({counter})"
                    counter += 1
                    
                    # Safety check to prevent infinite loop
                    if counter > 1000:
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Could not generate unique diagram name"
                        )
                
                if diagram_name != diagram_data.name:
                    logger.info(
                        "Diagram name already exists, using unique name",
                        original_name=diagram_data.name,
                        new_name=diagram_name
                    )
                
                # Create diagram
                diagram = Diagram(
                    model_id=model.id,
                    name=diagram_name,
                    description=diagram_data.description,
                    notation=diagram_data.notation_type,
                    notation_config={},
                    visible_concepts=[],
                    settings={},
                    created_by=current_user.id,
                )
                
                db.add(diagram)
                await db.commit()
                await db.refresh(diagram)
                
                # Success! Break out of retry loop
                break
                
            except IntegrityError as ie:
                # Race condition: another request created the same name
                await db.rollback()
                retry_count += 1
                
                if retry_count >= max_retries:
                    logger.error(f"Failed to create diagram after {max_retries} retries")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Failed to create diagram due to concurrent requests"
                    )
                
                logger.warning(
                    f"Race condition detected, retrying ({retry_count}/{max_retries})",
                    attempted_name=diagram_name
                )
                
                # Increment counter for next attempt
                diagram_name = f"{diagram_data.name} ({counter})"
                counter += 1
                
                # Small delay to reduce collision probability
                await asyncio.sleep(0.01 * retry_count)
        
        if not diagram:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create diagram"
            )
        
        logger.info(
            "Diagram created",
            diagram_id=str(diagram.id),
            diagram_name=diagram.name,
            model_id=str(model.id),
            user_id=str(current_user.id)
        )
        
        return diagram_to_response(diagram)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error creating diagram", error=str(e), error_type=type(e).__name__)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create diagram: {str(e)}"
        )


@router.get("/", response_model=List[DiagramResponse])
async def list_diagrams(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all diagrams for the current user"""
    try:
        result = await db.execute(
            select(Diagram)
            .where(Diagram.created_by == current_user.id)
            .offset(skip)
            .limit(limit)
            .order_by(Diagram.created_at.desc())
        )
        diagrams = result.scalars().all()
        
        logger.info("Diagrams listed", count=len(diagrams), user_id=str(current_user.id))
        
        return [diagram_to_response(d) for d in diagrams]
        
    except Exception as e:
        logger.error("Error listing diagrams", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list diagrams: {str(e)}"
        )


@router.get("/models/{model_id}/diagrams", response_model=List[DiagramResponse])
async def list_diagrams_by_model(
    model_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all diagrams for a specific model"""
    try:
        model_uuid = uuid.UUID(model_id)
        
        result = await db.execute(
            select(Diagram).where(Diagram.model_id == model_uuid)
        )
        diagrams = result.scalars().all()
        
        logger.info("Diagrams listed by model", model_id=model_id, count=len(diagrams))
        
        return [diagram_to_response(d) for d in diagrams]
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid model ID format"
        )
    except Exception as e:
        logger.error("Error listing diagrams", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list diagrams: {str(e)}"
        )


@router.get("/models/{model_id}/diagrams/{diagram_id}", response_model=DiagramResponse)
async def get_diagram_by_model(
    model_id: str,
    diagram_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific diagram within a specific model"""
    try:
        model_uuid = uuid.UUID(model_id)
        diagram_uuid = uuid.UUID(diagram_id)
        
        result = await db.execute(
            select(Diagram).where(
                Diagram.id == diagram_uuid,
                Diagram.model_id == model_uuid
            )
        )
        diagram = result.scalar_one_or_none()
        
        if not diagram:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Diagram not found"
            )
        
        logger.info("Diagram retrieved by model", model_id=model_id, diagram_id=diagram_id)
        
        return diagram_to_response(diagram)
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid model or diagram ID format"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting diagram", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get diagram: {str(e)}"
        )


@router.get("/{diagram_id}", response_model=DiagramResponse)
async def get_diagram(
    diagram_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get diagram by ID"""
    try:
        diagram_uuid = uuid.UUID(diagram_id)
        
        result = await db.execute(
            select(Diagram).where(Diagram.id == diagram_uuid)
        )
        diagram = result.scalar_one_or_none()
        
        if not diagram:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Diagram not found"
            )
        
        logger.info("Diagram retrieved", diagram_id=diagram_id)
        
        return diagram_to_response(diagram)
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid diagram ID format"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting diagram", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get diagram: {str(e)}"
        )


@router.put("/{diagram_id}", response_model=DiagramResponse)
async def update_diagram(
    diagram_id: str,
    diagram_data: DiagramUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update diagram"""
    try:
        diagram_uuid = uuid.UUID(diagram_id)
        
        result = await db.execute(
            select(Diagram).where(Diagram.id == diagram_uuid)
        )
        diagram = result.scalar_one_or_none()
        
        if not diagram:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Diagram not found"
            )
        
        # Update fields
        if diagram_data.name is not None:
            diagram.name = diagram_data.name
        if diagram_data.description is not None:
            diagram.description = diagram_data.description
        if diagram_data.notation_config is not None:
            diagram.notation_config = diagram_data.notation_config
        if diagram_data.settings is not None:
            diagram.settings = diagram_data.settings
        if diagram_data.visible_concepts is not None:
            diagram.visible_concepts = [
                uuid.UUID(c) if isinstance(c, str) else c 
                for c in diagram_data.visible_concepts
            ]
        
        diagram.updated_by = current_user.id
        diagram.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(diagram)
        
        logger.info("Updated diagram", diagram_id=diagram_id)
        
        return diagram_to_response(diagram)
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid diagram ID format"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating diagram", error=str(e))
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update diagram: {str(e)}"
        )


@router.delete("/{diagram_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_diagram(
    diagram_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete diagram (hard delete)"""
    try:
        diagram_uuid = uuid.UUID(diagram_id)
        
        result = await db.execute(
            select(Diagram).where(Diagram.id == diagram_uuid)
        )
        diagram = result.scalar_one_or_none()
        
        if not diagram:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Diagram not found"
            )
        
        await db.delete(diagram)
        await db.commit()
        
        logger.info("Deleted diagram", diagram_id=diagram_id)
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid diagram ID format"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting diagram", error=str(e))
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete diagram: {str(e)}"
        )


@router.post("/{diagram_id}/duplicate", response_model=DiagramResponse)
async def duplicate_diagram(
    diagram_id: str,
    new_name: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Duplicate an existing diagram"""
    try:
        diagram_uuid = uuid.UUID(diagram_id)
        
        result = await db.execute(
            select(Diagram).where(Diagram.id == diagram_uuid)
        )
        diagram = result.scalar_one_or_none()
        
        if not diagram:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Diagram not found"
            )
        
        # Create duplicate
        duplicate_name = new_name or f"{diagram.name} (Copy)"
        
        new_diagram = Diagram(
            model_id=diagram.model_id,
            name=duplicate_name,
            description=diagram.description,
            notation=diagram.notation,
            notation_config=diagram.notation_config,
            visible_concepts=diagram.visible_concepts.copy() if diagram.visible_concepts else [],
            settings=diagram.settings.copy() if diagram.settings else {},
            created_by=current_user.id,
        )
        
        db.add(new_diagram)
        await db.commit()
        await db.refresh(new_diagram)
        
        logger.info("Duplicated diagram", original_id=diagram_id, new_id=str(new_diagram.id))
        
        return diagram_to_response(new_diagram)
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid diagram ID format"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error duplicating diagram", error=str(e))
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to duplicate diagram: {str(e)}"
        )