# backend/app/api/v1/endpoints/diagrams.py
"""
Diagram Management Endpoints - COMPLETE AND FIXED
FIXED: Proper async/await handling to prevent greenlet errors
Path: backend/app/api/v1/endpoints/diagrams.py
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.exc import IntegrityError
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime
import uuid
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
    """Get user's personal workspace or create it - FIXED for async"""
    # Query with proper async handling
    stmt = select(Workspace).where(
        and_(
            Workspace.created_by == user.id,
            Workspace.type == WorkspaceType.PERSONAL
        )
    )
    result = await db.execute(stmt)
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
    await db.refresh(workspace)
    
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
    
    FIXED: Robust handling of duplicate model/diagram names with proper async
    """
    try:
        # Get or create personal workspace
        workspace = await get_or_create_personal_workspace(db, current_user)
        workspace_id = workspace.id
        
        # ====================================================================
        # STEP 1: Handle model creation/lookup
        # ====================================================================
        if diagram_data.model_id:
            # Use provided model
            try:
                model_uuid = uuid.UUID(diagram_data.model_id)
                stmt = select(Model).where(Model.id == model_uuid)
                result = await db.execute(stmt)
                model = result.scalar_one_or_none()
                
                if not model:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Model not found: {diagram_data.model_id}"
                    )
                    
                logger.info(
                    "Using existing model",
                    model_id=str(model.id),
                    model_name=model.name
                )
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid model ID format"
                )
        else:
            # Find unique model name with retry logic
            base_model_name = diagram_data.model_name or f"Model for {diagram_data.name}"
            model_name = base_model_name
            counter = 1
            max_attempts = 10
            model = None
            
            for attempt in range(max_attempts):
                # Check if model exists
                stmt = select(Model).where(
                    and_(
                        Model.workspace_id == workspace_id,
                        Model.name == model_name
                    )
                )
                result = await db.execute(stmt)
                existing_model = result.scalar_one_or_none()
                
                if existing_model:
                    # Model exists, use it
                    model = existing_model
                    logger.info(
                        "Using existing model",
                        model_id=str(model.id),
                        model_name=model.name,
                        attempt=attempt + 1
                    )
                    break
                
                # Try to create model
                try:
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
                        attempt=attempt + 1
                    )
                    break
                    
                except IntegrityError:
                    # Race condition
                    await db.rollback()
                    model_name = f"{base_model_name} ({counter})"
                    counter += 1
                    logger.warning(
                        "Model name conflict, retrying",
                        new_name=model_name,
                        attempt=attempt + 1
                    )
                    continue
            
            if not model:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Could not create or find model after {max_attempts} attempts"
                )
        
        # ====================================================================
        # STEP 2: Create diagram with unique name handling
        # ====================================================================
        diagram_name = diagram_data.name
        counter = 1
        max_attempts = 10
        diagram = None
        
        for attempt in range(max_attempts):
            # Check if diagram name exists
            stmt = select(Diagram).where(
                and_(
                    Diagram.model_id == model.id,
                    Diagram.name == diagram_name
                )
            )
            result = await db.execute(stmt)
            existing_diagram = result.scalar_one_or_none()
            
            if existing_diagram:
                # Name exists, try with counter
                diagram_name = f"{diagram_data.name} ({counter})"
                counter += 1
                logger.info(
                    "Diagram name exists, trying new name",
                    original_name=diagram_data.name,
                    new_name=diagram_name,
                    attempt=attempt + 1
                )
                continue
            
            # Try to create diagram
            try:
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
                
                if diagram_name != diagram_data.name:
                    logger.info(
                        "Created diagram with modified name",
                        original_name=diagram_data.name,
                        final_name=diagram_name,
                        diagram_id=str(diagram.id)
                    )
                else:
                    logger.info(
                        "Created diagram",
                        diagram_id=str(diagram.id),
                        name=diagram_name
                    )
                break
                
            except IntegrityError:
                await db.rollback()
                diagram_name = f"{diagram_data.name} ({counter})"
                counter += 1
                continue
        
        if not diagram:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Could not create diagram after {max_attempts} attempts"
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
        stmt = select(Diagram).where(
            Diagram.created_by == current_user.id
        ).offset(skip).limit(limit).order_by(Diagram.created_at.desc())
        
        result = await db.execute(stmt)
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
        
        stmt = select(Diagram).where(Diagram.model_id == model_uuid)
        result = await db.execute(stmt)
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


@router.get("/{diagram_id}", response_model=DiagramResponse)
async def get_diagram(
    diagram_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific diagram"""
    try:
        diagram_uuid = uuid.UUID(diagram_id)
        
        stmt = select(Diagram).where(Diagram.id == diagram_uuid)
        result = await db.execute(stmt)
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
        
        stmt = select(Diagram).where(Diagram.id == diagram_uuid)
        result = await db.execute(stmt)
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
        
        await db.commit()
        await db.refresh(diagram)
        
        logger.info("Diagram updated", diagram_id=diagram_id)
        
        return diagram_to_response(diagram)
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ID format"
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
    """Delete a diagram"""
    try:
        diagram_uuid = uuid.UUID(diagram_id)
        
        stmt = select(Diagram).where(Diagram.id == diagram_uuid)
        result = await db.execute(stmt)
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
        
        stmt = select(Diagram).where(Diagram.id == diagram_uuid)
        result = await db.execute(stmt)
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