# backend/app/api/v1/endpoints/diagrams.py
"""
Diagram Management Endpoints - COMPLETE AND FIXED
FIXED: Proper async/await handling and layout creation to prevent greenlet errors
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
from app.models.layout import Layout
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
            Workspace.type == WorkspaceType.PERSONAL,
            Workspace.deleted_at.is_(None)
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
    
    FIXED: Proper async session handling and layout creation
    """
    try:
        # Get or create personal workspace
        workspace = await get_or_create_personal_workspace(db, current_user)
        workspace_id = workspace.id
        
        # ====================================================================
        # STEP 1: Handle model creation/lookup
        # ====================================================================
        model = None
        if diagram_data.model_id:
            # Use provided model
            try:
                model_uuid = uuid.UUID(diagram_data.model_id)
                stmt = select(Model).where(
                    and_(
                        Model.id == model_uuid,
                        Model.deleted_at.is_(None)
                    )
                )
                result = await db.execute(stmt)
                model = result.scalar_one_or_none()
                
                if not model:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Model {diagram_data.model_id} not found"
                    )
                
                logger.info("Using existing model", model_id=str(model.id))
                
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid model_id format"
                )
        else:
            # Create new model
            model_name = diagram_data.model_name or diagram_data.name
            
            # Try to create model with unique name
            max_attempts = 10
            counter = 1
            
            for attempt in range(max_attempts):
                try:
                    current_model_name = model_name if counter == 1 else f"{model_name} ({counter})"
                    
                    model = Model(
                        name=current_model_name,
                        description=f"Model for {diagram_data.name}",
                        type=ModelType.LOGICAL,
                        status=ModelStatus.DRAFT,
                        workspace_id=workspace_id,
                        created_by=current_user.id,
                        settings={}
                    )
                    
                    db.add(model)
                    await db.flush()
                    await db.refresh(model)
                    
                    logger.info(
                        "Created model",
                        model_id=str(model.id),
                        name=current_model_name,
                        attempt=attempt + 1
                    )
                    break
                    
                except IntegrityError:
                    await db.rollback()
                    counter += 1
                    if attempt == max_attempts - 1:
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Could not create model after {max_attempts} attempts"
                        )
                    continue
        
        if not model:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create or find model"
            )
        
        # ====================================================================
        # STEP 2: Create diagram with unique name handling
        # ====================================================================
        diagram_name = diagram_data.name
        max_attempts = 10
        counter = 1
        diagram = None
        
        for attempt in range(max_attempts):
            try:
                # Generate unique name if needed
                current_diagram_name = diagram_name if counter == 1 else f"{diagram_name} ({counter})"
                
                # Create diagram
                diagram = Diagram(
                    name=current_diagram_name,
                    description=diagram_data.description,
                    model_id=model.id,
                    notation=diagram_data.notation_type,
                    notation_config={},
                    visible_concepts=[],
                    settings={},
                    created_by=current_user.id,
                )
                
                db.add(diagram)
                await db.flush()
                await db.refresh(diagram)
                
                logger.info(
                    "Created diagram",
                    diagram_id=str(diagram.id),
                    name=current_diagram_name,
                    notation=diagram_data.notation_type,
                    model_id=str(model.id),
                    attempt=attempt + 1
                )
                break
                
            except IntegrityError as e:
                await db.rollback()
                logger.warning(
                    "Diagram name conflict, retrying",
                    name=current_diagram_name,
                    attempt=attempt + 1,
                    error=str(e)
                )
                counter += 1
                
                if attempt == max_attempts - 1:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Could not create diagram after {max_attempts} attempts"
                    )
                continue
        
        if not diagram:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create diagram"
            )
        
        # ====================================================================
        # STEP 3: Create default layout (IMPORTANT - replaces DB trigger)
        # ====================================================================
        try:
            layout = Layout(
                diagram_id=diagram.id,
                name="Default Layout",
                description="Default manual layout",
                layout_engine="manual",
                layout_data={
                    "nodes": {},
                    "edges": {},
                    "constraints": {},
                    "viewport": {
                        "x": 0,
                        "y": 0,
                        "zoom": 1.0
                    }
                },
                is_default=True,
                created_by=current_user.id
            )
            
            db.add(layout)
            await db.flush()
            await db.refresh(layout)
            
            logger.info(
                "Created default layout",
                layout_id=str(layout.id),
                diagram_id=str(diagram.id)
            )
            
        except Exception as e:
            logger.error(
                "Failed to create default layout",
                diagram_id=str(diagram.id),
                error=str(e)
            )
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create default layout: {str(e)}"
            )
        
        # ====================================================================
        # STEP 4: Commit everything together
        # ====================================================================
        await db.commit()
        await db.refresh(diagram)
        
        logger.info(
            "Diagram creation complete",
            diagram_id=str(diagram.id),
            model_id=str(model.id),
            layout_id=str(layout.id)
        )
        
        return diagram_to_response(diagram)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error creating diagram",
            error=str(e),
            error_type=type(e).__name__,
            diagram_name=diagram_data.name if diagram_data else None
        )
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create diagram: {str(e)}"
        )


@router.get("/", response_model=List[DiagramResponse])
async def list_diagrams(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    model_id: Optional[str] = Query(None, description="Filter by model ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all diagrams for the current user"""
    try:
        stmt = select(Diagram).where(
            and_(
                Diagram.created_by == current_user.id,
                Diagram.deleted_at.is_(None)
            )
        )
        
        # Optional model filter
        if model_id:
            try:
                model_uuid = uuid.UUID(model_id)
                stmt = stmt.where(Diagram.model_id == model_uuid)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid model_id format"
                )
        
        stmt = stmt.offset(skip).limit(limit).order_by(Diagram.created_at.desc())
        
        result = await db.execute(stmt)
        diagrams = result.scalars().all()
        
        logger.info("Diagrams listed", count=len(diagrams), user_id=str(current_user.id))
        
        return [diagram_to_response(d) for d in diagrams]
        
    except HTTPException:
        raise
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
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid diagram_id format"
        )
    
    try:
        stmt = select(Diagram).where(
            and_(
                Diagram.id == diagram_uuid,
                Diagram.deleted_at.is_(None)
            )
        )
        result = await db.execute(stmt)
        diagram = result.scalar_one_or_none()
        
        if not diagram:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Diagram {diagram_id} not found"
            )
        
        # Check ownership
        if diagram.created_by != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this diagram"
            )
        
        logger.info("Diagram retrieved", diagram_id=diagram_id, user_id=str(current_user.id))
        
        return diagram_to_response(diagram)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error retrieving diagram", diagram_id=diagram_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve diagram: {str(e)}"
        )


@router.patch("/{diagram_id}", response_model=DiagramResponse)
async def update_diagram(
    diagram_id: str,
    update_data: DiagramUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a diagram"""
    try:
        diagram_uuid = uuid.UUID(diagram_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid diagram_id format"
        )
    
    try:
        stmt = select(Diagram).where(
            and_(
                Diagram.id == diagram_uuid,
                Diagram.deleted_at.is_(None)
            )
        )
        result = await db.execute(stmt)
        diagram = result.scalar_one_or_none()
        
        if not diagram:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Diagram {diagram_id} not found"
            )
        
        # Check ownership
        if diagram.created_by != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this diagram"
            )
        
        # Update fields
        if update_data.name is not None:
            diagram.name = update_data.name
        if update_data.description is not None:
            diagram.description = update_data.description
        if update_data.notation_config is not None:
            diagram.notation_config = update_data.notation_config
        if update_data.visible_concepts is not None:
            diagram.visible_concepts = [uuid.UUID(c) for c in update_data.visible_concepts]
        if update_data.settings is not None:
            diagram.settings = update_data.settings
        
        diagram.updated_by = current_user.id
        diagram.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(diagram)
        
        logger.info("Diagram updated", diagram_id=diagram_id, user_id=str(current_user.id))
        
        return diagram_to_response(diagram)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating diagram", diagram_id=diagram_id, error=str(e))
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
    """Soft delete a diagram"""
    try:
        diagram_uuid = uuid.UUID(diagram_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid diagram_id format"
        )
    
    try:
        stmt = select(Diagram).where(
            and_(
                Diagram.id == diagram_uuid,
                Diagram.deleted_at.is_(None)
            )
        )
        result = await db.execute(stmt)
        diagram = result.scalar_one_or_none()
        
        if not diagram:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Diagram {diagram_id} not found"
            )
        
        # Check ownership
        if diagram.created_by != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this diagram"
            )
        
        # Soft delete
        diagram.deleted_at = datetime.utcnow()
        
        await db.commit()
        
        logger.info("Diagram deleted", diagram_id=diagram_id, user_id=str(current_user.id))
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting diagram", diagram_id=diagram_id, error=str(e))
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete diagram: {str(e)}"
        )


@router.get("/{diagram_id}/layouts")
async def get_diagram_layouts(
    diagram_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all layouts for a diagram"""
    try:
        diagram_uuid = uuid.UUID(diagram_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid diagram_id format"
        )
    
    try:
        # Verify diagram exists and user has access
        stmt = select(Diagram).where(
            and_(
                Diagram.id == diagram_uuid,
                Diagram.deleted_at.is_(None)
            )
        )
        result = await db.execute(stmt)
        diagram = result.scalar_one_or_none()
        
        if not diagram:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Diagram {diagram_id} not found"
            )
        
        if diagram.created_by != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this diagram"
            )
        
        # Get layouts
        stmt = select(Layout).where(
            and_(
                Layout.diagram_id == diagram_uuid,
                Layout.deleted_at.is_(None)
            )
        ).order_by(Layout.is_default.desc(), Layout.created_at.desc())
        
        result = await db.execute(stmt)
        layouts = result.scalars().all()
        
        logger.info("Layouts retrieved", diagram_id=diagram_id, count=len(layouts))
        
        return [
            {
                "id": str(layout.id),
                "name": layout.name,
                "description": layout.description,
                "engine": layout.layout_engine,
                "is_default": layout.is_default,
                "layout_data": layout.layout_data,
                "created_at": layout.created_at,
                "updated_at": layout.updated_at
            }
            for layout in layouts
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error retrieving layouts", diagram_id=diagram_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve layouts: {str(e)}"
        )