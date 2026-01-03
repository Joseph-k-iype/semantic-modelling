# backend/app/api/v1/endpoints/diagrams.py
"""
Diagram Management Endpoints - COMPLETE FIX
Path: backend/app/api/v1/endpoints/diagrams.py

CRITICAL FIXES:
1. Transaction boundary management - commit Model before Diagram
2. Random graph_name generation - prevents collisions
3. Proper session rollback before retry
4. Removed invalid Model parameters
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
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
from app.models.layout import Layout, LayoutType
from app.models.model import Model
from app.models.workspace import Workspace, WorkspaceType
from app.models.user import User

# Dependencies
from app.api.deps import get_current_user

# Services
from app.services.semantic_model_service import SemanticModelService

logger = structlog.get_logger(__name__)
router = APIRouter()

# ============================================================================
# REQUEST/RESPONSE SCHEMAS
# ============================================================================

class DiagramCreateRequest(BaseModel):
    """Schema for creating a diagram"""
    name: str
    notation_type: str
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


class DiagramNodesEdgesUpdate(BaseModel):
    """Schema for updating diagram nodes and edges"""
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]


class DiagramResponse(BaseModel):
    """Diagram response schema"""
    id: str
    name: str
    notation: str
    notation_type: str
    graph_name: Optional[str] = None
    model_id: str
    description: Optional[str] = None
    notation_config: Dict[str, Any] = {}
    visible_concepts: List[str] = []
    settings: Dict[str, Any] = {}
    is_default: bool = False
    is_valid: bool = True
    validation_errors: List[str] = []
    created_by: str
    updated_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class DiagramListResponse(BaseModel):
    """List of diagrams response"""
    diagrams: List[DiagramResponse]
    total: int


# ============================================================================
# NOTATION MAPPING
# ============================================================================

NOTATION_MAPPING = {
    "ER": "ER",
    "ENTITY_RELATIONSHIP": "ER",
    "UML_CLASS": "UML_CLASS",
    "CLASS": "UML_CLASS",
    "UML_SEQUENCE": "UML_SEQUENCE",
    "SEQUENCE": "UML_SEQUENCE",
    "UML_ACTIVITY": "UML_ACTIVITY",
    "ACTIVITY": "UML_ACTIVITY",
    "UML_STATE": "UML_STATE",
    "STATE": "UML_STATE",
    "UML_COMPONENT": "UML_COMPONENT",
    "COMPONENT": "UML_COMPONENT",
    "UML_DEPLOYMENT": "UML_DEPLOYMENT",
    "DEPLOYMENT": "UML_DEPLOYMENT",
    "UML_PACKAGE": "UML_PACKAGE",
    "PACKAGE": "UML_PACKAGE",
    "BPMN": "BPMN",
    "BUSINESS_PROCESS": "BPMN"
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def normalize_notation_type(notation_type: str) -> str:
    """Normalize notation type to standard format"""
    if not notation_type:
        raise ValueError("Notation type is required")
    
    notation_upper = notation_type.upper().strip()
    if notation_upper in NOTATION_MAPPING:
        return NOTATION_MAPPING[notation_upper]
    raise ValueError(f"Unsupported notation type: '{notation_type}'")


def get_model_type_from_notation(notation: str) -> str:
    """Get model type string from notation"""
    if notation == "ER":
        return "ER"
    elif notation.startswith("UML_"):
        return notation
    elif notation == "BPMN":
        return "BPMN"
    else:
        return "MIXED"


def diagram_to_response(diagram: Diagram) -> DiagramResponse:
    """Convert diagram model to response"""
    return DiagramResponse(
        id=str(diagram.id),
        name=diagram.name,
        notation=diagram.notation,
        notation_type=diagram.notation,
        graph_name=diagram.graph_name,
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
            Workspace.type == WorkspaceType.PERSONAL,
            Workspace.created_by == user.id,
            Workspace.deleted_at.is_(None)
        )
    )
    result = await db.execute(stmt)
    workspace = result.scalar_one_or_none()
    
    if workspace:
        logger.info(f"Found existing workspace for user {user.username}")
        return workspace
    
    safe_username = re.sub(r'[^a-z0-9-]', '', user.username.lower().replace('_', '-'))
    
    workspace = Workspace(
        name=f"{user.username}'s Personal Workspace",
        slug=f"{safe_username}-personal-{uuid.uuid4().hex[:8]}",
        description="Personal workspace",
        type=WorkspaceType.PERSONAL,
        is_active=True,
        created_by=user.id,
        updated_by=user.id,
        settings={},
        meta_data={}
    )
    
    try:
        db.add(workspace)
        await db.commit()
        await db.refresh(workspace)
        
        logger.info(
            "Created personal workspace",
            workspace_id=str(workspace.id),
            user_id=str(user.id),
            username=user.username
        )
        
        return workspace
        
    except IntegrityError as e:
        await db.rollback()
        logger.error(f"Failed to create workspace: {str(e)}")
        
        stmt = select(Workspace).where(
            and_(
                Workspace.type == WorkspaceType.PERSONAL,
                Workspace.created_by == user.id,
                Workspace.deleted_at.is_(None)
            )
        )
        result = await db.execute(stmt)
        workspace = result.scalar_one_or_none()
        
        if workspace:
            return workspace
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create or retrieve personal workspace: {str(e)}"
        )


def sanitize_for_graph_name(text: str) -> str:
    """Sanitize text for use in graph name"""
    text = text.replace(" ", "_").replace("-", "_")
    text = re.sub(r'[^a-zA-Z0-9_]', '', text)
    return text.lower()[:50]


async def create_or_get_model(
    db: AsyncSession,
    workspace: Workspace,
    user: User,
    model_id: Optional[str],
    model_name: str,
    diagram_name: str,
    model_type: str
) -> Model:
    """
    Create or get model - Handles Model in its own transaction
    """
    if model_id:
        try:
            model_uuid = uuid.UUID(model_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid model_id format"
            )
        
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
                detail=f"Model {model_id} not found"
            )
        
        if model.created_by != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to use this model"
            )
        
        return model
    
    # Create new model with unique graph_id
    safe_username = sanitize_for_graph_name(user.username)
    safe_workspace = sanitize_for_graph_name(workspace.name)
    safe_model = sanitize_for_graph_name(model_name)
    # CRITICAL FIX: Add random component to ensure uniqueness
    model_graph_id = f"model_{safe_username}_{safe_workspace}_{safe_model}_{uuid.uuid4().hex[:8]}"
    
    model = Model(
        workspace_id=workspace.id,
        name=model_name,
        description=f"Model for {diagram_name}",
        model_type=model_type,
        graph_id=model_graph_id,
        meta_data={},
        settings={},
        validation_rules=[],
        is_published=False,
        created_by=user.id,
        updated_by=user.id
    )
    
    try:
        db.add(model)
        await db.commit()
        await db.refresh(model)
        
        logger.info(
            "Created new model",
            model_id=str(model.id),
            model_name=model_name,
            model_type=model_type,
            graph_id=model_graph_id
        )
        
        return model
        
    except IntegrityError as e:
        await db.rollback()
        logger.error(f"Failed to create model: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create model: {str(e)}"
        )


async def create_diagram_with_retry(
    db: AsyncSession,
    model: Model,
    workspace: Workspace,
    user: User,
    diagram_name: str,
    description: Optional[str],
    normalized_notation: str,
    max_attempts: int = 5
) -> Diagram:
    """
    Create diagram with automatic retry for name conflicts
    
    CRITICAL FIX: Each attempt gets unique graph_name with random component
    """
    safe_username = sanitize_for_graph_name(user.username)
    safe_workspace = sanitize_for_graph_name(workspace.name)
    
    for attempt in range(max_attempts):
        try:
            # Generate unique name for this attempt
            if attempt == 0:
                current_name = diagram_name
            else:
                current_name = f"{diagram_name} ({attempt})"
            
            # CRITICAL FIX: Generate unique graph_name with random component
            safe_diagram = sanitize_for_graph_name(current_name)
            graph_name = f"user_{safe_username}_workspace_{safe_workspace}_diagram_{safe_diagram}_{uuid.uuid4().hex[:8]}"
            
            # Create diagram
            diagram = Diagram(
                model_id=model.id,
                name=current_name,
                description=description,
                notation=normalized_notation,
                graph_name=graph_name,
                notation_config={},
                visible_concepts=[],
                settings={},
                validation_errors=[],
                is_valid=True,
                is_default=True,
                created_by=user.id,
                updated_by=user.id
            )
            
            db.add(diagram)
            await db.commit()
            await db.refresh(diagram)
            
            logger.info(
                "Created diagram successfully",
                diagram_id=str(diagram.id),
                diagram_name=current_name,
                notation=normalized_notation,
                graph_name=graph_name,
                attempt=attempt + 1
            )
            
            return diagram
            
        except IntegrityError as e:
            # CRITICAL FIX: Rollback session before retry
            await db.rollback()
            
            error_msg = str(e)
            
            # Check if it's a name conflict (not foreign key or other errors)
            if "diagrams_unique_name" in error_msg or "duplicate key" in error_msg.lower():
                logger.warning(
                    f"Diagram name conflict, retrying with different name",
                    attempt=attempt + 1,
                    max_attempts=max_attempts,
                    error=error_msg[:200]
                )
                
                if attempt < max_attempts - 1:
                    continue
                else:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Could not create diagram with unique name after {max_attempts} attempts"
                    )
            else:
                # Not a name conflict - raise immediately
                logger.error(
                    "Failed to create diagram - non-recoverable error",
                    error=error_msg,
                    model_id=str(model.id)
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to create diagram: {str(e)}"
                )
    
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Failed to create diagram after maximum retries"
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
    """Create a new diagram with FalkorDB graph integration"""
    try:
        # Normalize notation type
        try:
            normalized_notation = normalize_notation_type(diagram_data.notation_type)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        
        # Get model type from notation
        model_type = get_model_type_from_notation(normalized_notation)
        
        # Get or create personal workspace (commits in its own transaction)
        try:
            workspace = await get_or_create_personal_workspace(db, current_user)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get/create workspace: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create workspace: {str(e)}"
            )
        
        logger.info(
            "Using workspace for diagram",
            workspace_id=str(workspace.id),
            workspace_name=workspace.name
        )
        
        # Create or get model (commits in its own transaction)
        model_name = diagram_data.model_name or f"{diagram_data.name} Model"
        try:
            model = await create_or_get_model(
                db=db,
                workspace=workspace,
                user=current_user,
                model_id=diagram_data.model_id,
                model_name=model_name,
                diagram_name=diagram_data.name,
                model_type=model_type
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to create/get model: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create model: {str(e)}"
            )
        
        # Create diagram with retry logic (separate transaction)
        try:
            diagram = await create_diagram_with_retry(
                db=db,
                model=model,
                workspace=workspace,
                user=current_user,
                diagram_name=diagram_data.name,
                description=diagram_data.description,
                normalized_notation=normalized_notation,
                max_attempts=5
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to create diagram: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create diagram: {str(e)}"
            )
        
        # Create default layout (non-critical)
        try:
            layout = Layout(
                diagram_id=diagram.id,
                name="Default Layout",
                description="Default manual layout",
                layout_type=LayoutType.MANUAL,
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
            
            logger.info(
                "Created default layout",
                layout_id=str(layout.id),
                diagram_id=str(diagram.id)
            )
        except Exception as layout_error:
            await db.rollback()
            logger.error(
                "Failed to create layout (non-critical)",
                error=str(layout_error)
            )
        
        # Refresh diagram to get latest state
        await db.refresh(diagram)
        
        # Initialize FalkorDB graph (non-critical)
        try:
            semantic_service = SemanticModelService()
            
            await semantic_service.sync_diagram_to_graph(
                db=db,
                diagram_id=str(diagram.id),
                user_id=str(current_user.id),
                workspace_id=str(workspace.id),
                nodes=[],
                edges=[]
            )
            
            logger.info(
                "Initialized FalkorDB graph",
                graph_name=diagram.graph_name
            )
        except Exception as graph_error:
            logger.warning(
                "FalkorDB initialization failed (non-critical)",
                error=str(graph_error)
            )
        
        return diagram_to_response(diagram)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error creating diagram", error=str(e))
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create diagram: {str(e)}"
        )


@router.get("/", response_model=DiagramListResponse)
async def list_diagrams(
    model_id: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List diagrams with optional model filter"""
    try:
        query = select(Diagram).where(
            and_(
                Diagram.created_by == current_user.id,
                Diagram.deleted_at.is_(None)
            )
        )
        
        if model_id:
            try:
                model_uuid = uuid.UUID(model_id)
                query = query.where(Diagram.model_id == model_uuid)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid model_id format"
                )
        
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        query = query.offset(skip).limit(limit).order_by(Diagram.created_at.desc())
        result = await db.execute(query)
        diagrams = result.scalars().all()
        
        return DiagramListResponse(
            diagrams=[diagram_to_response(d) for d in diagrams],
            total=total
        )
        
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
        
        if diagram.created_by != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this diagram"
            )
        
        return diagram_to_response(diagram)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting diagram", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get diagram: {str(e)}"
        )


@router.patch("/{diagram_id}", response_model=DiagramResponse)
async def update_diagram(
    diagram_id: str,
    update_data: DiagramUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update diagram metadata"""
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
        
        if diagram.created_by != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this diagram"
            )
        
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
        
        logger.info(
            "Updated diagram",
            diagram_id=str(diagram.id),
            user_id=str(current_user.id)
        )
        
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


@router.delete("/{diagram_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_diagram(
    diagram_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Soft delete diagram"""
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
        
        if diagram.created_by != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this diagram"
            )
        
        diagram.deleted_at = datetime.utcnow()
        await db.commit()
        
        logger.info(
            "Deleted diagram",
            diagram_id=str(diagram.id),
            user_id=str(current_user.id)
        )
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting diagram", error=str(e))
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete diagram: {str(e)}"
        )


@router.post("/{diagram_id}/sync", status_code=status.HTTP_200_OK)
async def sync_diagram_to_graph(
    diagram_id: str,
    sync_data: DiagramNodesEdgesUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Sync diagram nodes and edges to FalkorDB"""
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
        
        if diagram.created_by != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to sync this diagram"
            )
        
        stmt = select(Model).where(Model.id == diagram.model_id)
        result = await db.execute(stmt)
        model = result.scalar_one_or_none()
        
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Model not found"
            )
        
        semantic_service = SemanticModelService()
        
        stats = await semantic_service.sync_diagram_to_graph(
            db=db,
            diagram_id=str(diagram.id),
            user_id=str(current_user.id),
            workspace_id=str(model.workspace_id),
            nodes=sync_data.nodes,
            edges=sync_data.edges
        )
        
        logger.info(
            "Synced diagram to graph",
            diagram_id=str(diagram.id),
            stats=stats
        )
        
        return {
            "message": "Diagram synced successfully",
            "stats": stats
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error syncing diagram", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync diagram: {str(e)}"
        )