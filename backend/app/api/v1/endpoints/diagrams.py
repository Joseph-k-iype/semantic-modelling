# backend/app/api/v1/endpoints/diagrams.py
"""
Diagram Management Endpoints - COMPLETE WITH ALL IMPORTS
Path: backend/app/api/v1/endpoints/diagrams.py

CRITICAL FIXES:
1. All necessary imports included
2. Uses LayoutType enum correctly
3. Uses 'notation' field (not 'notation_type')
4. Generates and stores graph_name
5. Complete error handling
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
import re

# Database session
from app.db.session import get_db

# Models
from app.models.diagram import Diagram
from app.models.layout import Layout, LayoutType  # CRITICAL: Import LayoutType enum
from app.models.model import Model, ModelType, ModelStatus
from app.models.workspace import Workspace, WorkspaceType
from app.models.user import User

# Dependencies
from app.api.deps import get_current_user

logger = structlog.get_logger(__name__)
router = APIRouter()

# ============================================================================
# REQUEST/RESPONSE SCHEMAS
# ============================================================================

class DiagramCreateRequest(BaseModel):
    """Schema for creating a diagram"""
    name: str
    notation_type: str  # Frontend sends this, we normalize to 'notation'
    description: Optional[str] = None
    model_id: Optional[str] = None
    model_name: Optional[str] = None


class DiagramUpdateRequest(BaseModel):
    """Schema for updating a diagram"""
    name: Optional[str] = None
    description: Optional[str] = None
    notation_config: Optional[Dict[str, Any]] = None
    visible_concepts: Optional[List[str]] = None
    settings: Optional[Dict[str, Any]] = None


class DiagramResponse(BaseModel):
    """Schema for diagram response"""
    id: str
    name: str
    notation: str  # Return as 'notation'
    notation_type: str  # Also return as 'notation_type' for frontend compatibility
    graph_name: Optional[str] = None  # STRATEGIC FIX: Return graph reference
    model_id: str
    description: Optional[str] = None
    notation_config: Dict[str, Any]
    visible_concepts: List[str]
    settings: Dict[str, Any]
    is_default: bool
    is_valid: bool
    validation_errors: List[Any]
    created_by: str
    updated_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# ============================================================================
# NOTATION MAPPING
# ============================================================================

NOTATION_MAPPING = {
    'ER': 'ER',
    'LOGICAL': 'ER',
    'PHYSICAL': 'ER',
    'CONCEPTUAL': 'ER',
    'UML_CLASS': 'UML_CLASS',
    'UML-CLASS': 'UML_CLASS',
    'UML_SEQUENCE': 'UML_SEQUENCE',
    'UML-SEQUENCE': 'UML_SEQUENCE',
    'UML_ACTIVITY': 'UML_ACTIVITY',
    'UML-ACTIVITY': 'UML_ACTIVITY',
    'UML_STATE_MACHINE': 'UML_STATE',
    'UML-STATE-MACHINE': 'UML_STATE',
    'UML_STATE': 'UML_STATE',
    'UML_COMPONENT': 'UML_COMPONENT',
    'UML-COMPONENT': 'UML_COMPONENT',
    'UML_DEPLOYMENT': 'UML_DEPLOYMENT',
    'UML-DEPLOYMENT': 'UML_DEPLOYMENT',
    'UML_PACKAGE': 'UML_PACKAGE',
    'UML-PACKAGE': 'UML_PACKAGE',
    'BPMN': 'BPMN',
    'CUSTOM': 'MIXED',
}


def normalize_notation_type(notation_type: str) -> str:
    """Normalize notation type from frontend to database format"""
    notation_upper = notation_type.upper().strip()
    if notation_upper in NOTATION_MAPPING:
        return NOTATION_MAPPING[notation_upper]
    raise ValueError(f"Unsupported notation type: '{notation_type}'")


def get_model_type_from_notation(notation: str) -> ModelType:
    """Get model type from notation"""
    if notation == "ER":
        return ModelType.ER
    elif notation.startswith("UML_"):
        return ModelType.UML
    elif notation == "BPMN":
        return ModelType.BPMN
    else:
        return ModelType.MIXED


def diagram_to_response(diagram: Diagram) -> DiagramResponse:
    """Convert diagram model to response"""
    return DiagramResponse(
        id=str(diagram.id),
        name=diagram.name,
        notation=diagram.notation,  # CRITICAL: Use 'notation'
        notation_type=diagram.notation,  # Also provide as 'notation_type' for frontend
        graph_name=diagram.graph_name,  # STRATEGIC FIX: Include graph reference
        model_id=str(diagram.model_id),
        description=diagram.description,
        notation_config=diagram.notation_config or {},
        visible_concepts=[str(c) for c in (diagram.visible_concepts or [])],
        settings=diagram.settings or {},
        is_default=diagram.is_default,
        is_valid=diagram.is_valid,
        validation_errors=diagram.validation_errors or [],
        created_by=str(diagram.created_by),
        updated_by=str(diagram.updated_by) if diagram.updated_by else None,
        created_at=diagram.created_at,
        updated_at=diagram.updated_at
    )


async def get_or_create_personal_workspace(db: AsyncSession, user: User) -> Workspace:
    """Get or create personal workspace for user"""
    stmt = select(Workspace).where(
        and_(
            Workspace.created_by == user.id,
            Workspace.workspace_type == WorkspaceType.PERSONAL,
            Workspace.deleted_at.is_(None)
        )
    )
    result = await db.execute(stmt)
    workspace = result.scalar_one_or_none()
    
    if not workspace:
        workspace = Workspace(
            name=f"{user.username}'s Workspace",
            description="Personal workspace",
            workspace_type=WorkspaceType.PERSONAL,
            created_by=user.id,
            updated_by=user.id
        )
        db.add(workspace)
        await db.flush()
        await db.refresh(workspace)
    
    return workspace


def sanitize_for_graph_name(text: str) -> str:
    """Sanitize text for use in graph name"""
    # Replace spaces and dashes with underscores
    text = text.replace(" ", "_").replace("-", "_")
    # Remove special characters, keep only alphanumeric and underscores
    text = re.sub(r'[^a-zA-Z0-9_]', '', text)
    # Lowercase and truncate
    return text.lower()[:50]


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
    Create a new diagram
    
    STRATEGIC FIXES:
    1. Uses 'notation' field (not 'notation_type')
    2. Generates graph_name for FalkorDB
    3. Stores graph_name in diagram
    4. Uses LayoutType enum correctly
    """
    try:
        # Normalize notation type
        try:
            normalized_notation = normalize_notation_type(diagram_data.notation_type)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        
        # Get or create personal workspace
        workspace = await get_or_create_personal_workspace(db, current_user)
        workspace_id = workspace.id
        
        # Get or create model
        model = None
        if diagram_data.model_id:
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
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid model_id format"
                )
        
        if not model:
            # Create new model
            model_name = diagram_data.model_name or f"{diagram_data.name} Model"
            model_type = get_model_type_from_notation(normalized_notation)
            
            safe_username = sanitize_for_graph_name(current_user.username)
            safe_model_name = sanitize_for_graph_name(model_name)
            graph_id = f"user_{safe_username}_model_{safe_model_name}_{uuid.uuid4().hex[:8]}"
            
            model = Model(
                workspace_id=workspace_id,
                name=model_name,
                description=diagram_data.description,
                model_type=model_type,
                graph_id=graph_id,
                meta_data={},
                settings={},
                validation_rules=[],
                is_published=False,
                created_by=current_user.id,
                updated_by=current_user.id
            )
            
            db.add(model)
            await db.flush()
            await db.refresh(model)
            
            logger.info(
                "Created new model",
                model_id=str(model.id),
                model_name=model_name,
                model_type=model_type
            )
        
        # STRATEGIC FIX: Generate graph name
        # Format: user_{username}_workspace_{workspace}_diagram_{diagram_name}
        safe_username = sanitize_for_graph_name(current_user.username)
        safe_workspace = sanitize_for_graph_name(workspace.name)
        safe_diagram = sanitize_for_graph_name(diagram_data.name)
        
        graph_name = f"user_{safe_username}_workspace_{safe_workspace}_diagram_{safe_diagram}"
        
        # Create diagram with unique name handling
        diagram = None
        max_attempts = 3
        counter = 0
        
        for attempt in range(max_attempts):
            try:
                diagram_name = diagram_data.name
                if counter > 0:
                    diagram_name = f"{diagram_data.name} ({counter})"
                    # Update graph name too
                    safe_diagram = sanitize_for_graph_name(diagram_name)
                    graph_name = f"user_{safe_username}_workspace_{safe_workspace}_diagram_{safe_diagram}"
                
                # CRITICAL FIX: Use 'notation' field
                diagram = Diagram(
                    model_id=model.id,
                    name=diagram_name,
                    description=diagram_data.description,
                    notation=normalized_notation,  # CRITICAL: Use 'notation'
                    graph_name=graph_name,  # STRATEGIC FIX: Store graph reference
                    notation_config={},
                    visible_concepts=[],
                    settings={},
                    validation_errors=[],
                    is_valid=True,
                    is_default=True,
                    created_by=current_user.id,
                    updated_by=current_user.id
                )
                
                db.add(diagram)
                await db.flush()
                await db.refresh(diagram)
                
                logger.info(
                    "✅ Created diagram with graph reference",
                    diagram_id=str(diagram.id),
                    diagram_name=diagram_name,
                    notation=normalized_notation,
                    graph_name=graph_name
                )
                break
                
            except IntegrityError:
                await db.rollback()
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
        
        # Create default layout - CRITICAL: Use LayoutType enum
        try:
            layout = Layout(
                diagram_id=diagram.id,
                name="Default Layout",
                description="Default manual layout",
                layout_type=LayoutType.MANUAL,  # CRITICAL: Use enum, not string
                layout_data={
                    "nodes": {},
                    "edges": {},
                    "constraints": {},
                    "viewport": {"x": 0, "y": 0, "zoom": 1.0}
                },
                is_active=True,
                is_auto_apply=False,
                created_by=current_user.id
            )
            
            db.add(layout)
            await db.commit()
            await db.refresh(diagram)
            
            logger.info(
                "Created default layout",
                layout_id=str(layout.id),
                diagram_id=str(diagram.id)
            )
        except Exception as layout_error:
            logger.error(
                "Failed to create layout (non-critical)",
                error=str(layout_error)
            )
            await db.commit()
            await db.refresh(diagram)
        
        logger.info(
            "Diagram creation complete",
            diagram_id=str(diagram.id)
        )
        
        return diagram_to_response(diagram)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error creating diagram",
            error=str(e),
            error_type=type(e).__name__
        )
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create diagram: {str(e)}"
        )


@router.patch("/{diagram_id}", response_model=DiagramResponse)
async def update_diagram(
    diagram_id: str,
    update_data: DiagramUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update diagram
    
    STRATEGIC FIX: Syncs to FalkorDB when notation_config changes
    """
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
        
        # STRATEGIC FIX: Sync to FalkorDB if notation_config changed
        if update_data.notation_config is not None:
            nodes = diagram.notation_config.get("nodes", [])
            edges = diagram.notation_config.get("edges", [])
            
            if nodes or edges:
                try:
                    from app.services.semantic_model_service import SemanticModelService
                    
                    # Get model for workspace_id
                    result = await db.execute(
                        select(Model).where(Model.id == diagram.model_id)
                    )
                    model = result.scalar_one_or_none()
                    
                    if model:
                        semantic_service = SemanticModelService()
                        sync_stats = await semantic_service.sync_diagram_to_graph(
                            db,
                            str(diagram.id),
                            str(current_user.id),
                            str(model.workspace_id),
                            nodes,
                            edges
                        )
                        
                        logger.info(
                            "✅ Diagram synced to FalkorDB",
                            diagram_id=str(diagram.id),
                            graph_name=diagram.graph_name,
                            stats=sync_stats
                        )
                except Exception as sync_error:
                    logger.warning(
                        "Failed to sync to FalkorDB (non-critical)",
                        error=str(sync_error)
                    )
        
        logger.info("Diagram updated", diagram_id=diagram_id)
        
        return diagram_to_response(diagram)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating diagram", error=str(e))
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update diagram: {str(e)}"
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
        
        return diagram_to_response(diagram)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error retrieving diagram", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve diagram: {str(e)}"
        )


@router.delete("/{diagram_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_diagram(
    diagram_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete diagram
    
    STRATEGIC FIX: Also deletes the FalkorDB graph
    """
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
        
        # STRATEGIC FIX: Delete FalkorDB graph
        if diagram.graph_name:
            try:
                from app.services.semantic_model_service import SemanticModelService
                
                semantic_service = SemanticModelService()
                await semantic_service.delete_diagram_graph(diagram.graph_name)
                
                logger.info(
                    "Deleted FalkorDB graph",
                    diagram_id=diagram_id,
                    graph_name=diagram.graph_name
                )
            except Exception as graph_error:
                logger.warning(
                    "Failed to delete FalkorDB graph (non-critical)",
                    error=str(graph_error)
                )
        
        # Soft delete
        diagram.deleted_at = datetime.utcnow()
        diagram.updated_by = current_user.id
        
        await db.commit()
        
        logger.info("Diagram deleted", diagram_id=diagram_id)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting diagram", error=str(e))
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete diagram: {str(e)}"
        )


@router.get("/", response_model=List[DiagramResponse])
async def list_diagrams(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    model_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List diagrams with optional filters"""
    try:
        query = select(Diagram).where(Diagram.deleted_at.is_(None))
        
        if model_id:
            model_uuid = uuid.UUID(model_id)
            query = query.where(Diagram.model_id == model_uuid)
        
        query = query.offset(skip).limit(limit).order_by(Diagram.created_at.desc())
        
        result = await db.execute(query)
        diagrams = result.scalars().all()
        
        return [diagram_to_response(d) for d in diagrams]
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid UUID format"
        )
    except Exception as e:
        logger.error("Error listing diagrams", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list diagrams: {str(e)}"
        )