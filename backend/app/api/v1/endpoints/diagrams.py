# backend/app/api/v1/endpoints/diagrams.py
"""
Diagram Management Endpoints - FULLY FIXED
Path: backend/app/api/v1/endpoints/diagrams.py

CRITICAL FIXES:
1. Changed 'notation_type' to 'notation' when creating Diagram objects
2. Removed 'is_archived' from Model creation (doesn't exist in Model class)
3. Added comprehensive FalkorDB synchronization
4. Store diagram with username, diagram name, and workspace name in FalkorDB
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
# NOTATION MAPPING - Maps frontend notation types to database values
# ============================================================================

NOTATION_MAPPING = {
    # ER and Data Modeling
    'ER': 'ER',
    'LOGICAL': 'ER',
    'PHYSICAL': 'ER',
    'CONCEPTUAL': 'ER',
    
    # UML Diagrams
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
    'UML_INTERACTION': 'UML_SEQUENCE',
    'UML-INTERACTION': 'UML_SEQUENCE',
    
    # BPMN
    'BPMN': 'BPMN',
    
    # Custom
    'CUSTOM': 'MIXED',
}


def normalize_notation_type(notation_type: str) -> str:
    """
    Normalize notation type from frontend to database format
    
    Args:
        notation_type: Frontend notation type (can be various formats)
        
    Returns:
        Database-compatible notation type
        
    Raises:
        ValueError: If notation type is not supported
    """
    notation_upper = notation_type.upper().strip()
    
    if notation_upper in NOTATION_MAPPING:
        return NOTATION_MAPPING[notation_upper]
    
    raise ValueError(
        f"Unsupported notation type: '{notation_type}'. "
        f"Supported types: {', '.join(sorted(set(NOTATION_MAPPING.keys())))}"
    )


def get_model_type_from_notation(notation: str) -> str:
    """
    Determine model type from notation
    
    Args:
        notation: Normalized notation type
        
    Returns:
        Model type string that matches Model.model_type column
    """
    if notation.startswith('UML_'):
        return 'UML_CLASS'
    elif notation == 'BPMN':
        return 'BPMN'
    elif notation == 'ER':
        return 'ER'
    else:
        return 'MIXED'


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


async def sync_diagram_to_falkordb(
    diagram: Diagram,
    model: Model,
    workspace: Workspace,
    user: User
) -> Dict[str, Any]:
    """
    Sync diagram information to FalkorDB
    
    Creates a Diagram node in FalkorDB with:
    - username
    - diagram name
    - workspace name
    - model name
    - notation type
    
    Returns:
        Sync result with success status and details
    """
    result = {
        "success": False,
        "falkordb_available": False,
        "graph_name": None,
        "node_created": False,
        "error": None
    }
    
    try:
        from app.graph.client import get_graph_client
        
        graph_client = get_graph_client()
        
        if not graph_client or not graph_client.is_connected():
            logger.warning("FalkorDB not available, skipping diagram sync")
            result["error"] = "FalkorDB not connected"
            return result
        
        result["falkordb_available"] = True
        
        # Generate graph name with username and workspace
        safe_username = str(user.username).replace("-", "_").replace("@", "_at_").replace(".", "_")
        safe_workspace = str(workspace.name).replace(" ", "_").replace("-", "_")
        graph_name = f"user_{safe_username}_workspace_{safe_workspace}"
        result["graph_name"] = graph_name
        
        # Create diagram node in FalkorDB
        diagram_properties = {
            "id": str(diagram.id),
            "name": diagram.name,
            "diagram_name": diagram.name,
            "username": user.username,
            "user_email": user.email,
            "workspace_name": workspace.name,
            "workspace_id": str(workspace.id),
            "model_id": str(model.id),
            "model_name": model.name,
            "notation": diagram.notation,
            "notation_type": diagram.notation,
            "description": diagram.description or "",
            "created_at": diagram.created_at.isoformat() if diagram.created_at else datetime.utcnow().isoformat(),
            "node_type": "Diagram"
        }
        
        # Create Cypher query to merge diagram node
        query = """
        MERGE (d:Diagram {id: $id})
        SET d.name = $name,
            d.diagram_name = $diagram_name,
            d.username = $username,
            d.user_email = $user_email,
            d.workspace_name = $workspace_name,
            d.workspace_id = $workspace_id,
            d.model_id = $model_id,
            d.model_name = $model_name,
            d.notation = $notation,
            d.notation_type = $notation_type,
            d.description = $description,
            d.created_at = $created_at,
            d.node_type = $node_type,
            d.updated_at = timestamp()
        RETURN d
        """
        
        # Execute query
        graph_client.execute_query(graph_name, query, diagram_properties)
        
        result["success"] = True
        result["node_created"] = True
        
        logger.info(
            "✅ Diagram synced to FalkorDB",
            diagram_id=str(diagram.id),
            diagram_name=diagram.name,
            username=user.username,
            workspace_name=workspace.name,
            graph_name=graph_name,
            notation=diagram.notation
        )
        
    except ImportError:
        logger.warning("FalkorDB library not installed, skipping sync")
        result["error"] = "FalkorDB library not installed"
    except Exception as e:
        logger.error("Failed to sync diagram to FalkorDB", error=str(e), error_type=type(e).__name__)
        result["error"] = str(e)
    
    return result


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
    
    FIXED: 
    - Uses 'notation' field (not 'notation_type') when creating Diagram
    - Removed 'is_archived' from Model creation (doesn't exist in Model class)
    - Syncs to FalkorDB with username, diagram name, and workspace name
    """
    try:
        # Normalize notation type
        try:
            normalized_notation = normalize_notation_type(diagram_data.notation_type)
            logger.info(
                "Normalized notation type",
                input=diagram_data.notation_type,
                output=normalized_notation
            )
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
        
        # Create new model if needed
        if not model:
            model_name = diagram_data.model_name or f"{diagram_data.name} Model"
            model_type = get_model_type_from_notation(normalized_notation)
            
            # Generate unique graph_id for FalkorDB
            safe_username = str(current_user.username).replace("-", "_")
            safe_model_name = model_name.replace(" ", "_").replace("-", "_")
            graph_id = f"user_{safe_username}_model_{safe_model_name}_{uuid.uuid4().hex[:8]}"
            
            # CRITICAL FIX: Removed is_archived (doesn't exist in Model class)
            # Model class only has: is_published, published_at, published_version
            model = Model(
                workspace_id=workspace_id,
                name=model_name,
                description=diagram_data.description,
                model_type=model_type,
                graph_id=graph_id,
                meta_data={},
                settings={},
                validation_rules=[],
                is_published=False,  # This exists
                # is_archived=False,  # REMOVED - this doesn't exist
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
        
        # Create diagram with CORRECT field name 'notation' (not 'notation_type')
        diagram = None
        max_attempts = 3
        counter = 0
        
        for attempt in range(max_attempts):
            try:
                diagram_name = diagram_data.name
                if counter > 0:
                    diagram_name = f"{diagram_data.name} ({counter})"
                
                # CRITICAL FIX: Use 'notation' field name (not 'notation_type')
                diagram = Diagram(
                    model_id=model.id,
                    name=diagram_name,
                    description=diagram_data.description,
                    notation=normalized_notation,  # FIXED: was 'notation_type'
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
                    "Created diagram",
                    diagram_id=str(diagram.id),
                    diagram_name=diagram_name,
                    notation=normalized_notation
                )
                break
                
            except IntegrityError as e:
                await db.rollback()
                logger.warning(
                    "Diagram name conflict, retrying",
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
        
        # Create default layout
        try:
            layout = Layout(
                diagram_id=diagram.id,
                name="Default Layout",
                description="Default manual layout",
                layout_type="MANUAL",
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
                is_active=True,
                is_auto_apply=False,
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
        
        # Commit to database
        await db.commit()
        await db.refresh(diagram)
        
        logger.info(
            "Diagram creation complete",
            diagram_id=str(diagram.id),
            model_id=str(model.id),
            layout_id=str(layout.id),
            notation=normalized_notation
        )
        
        # Sync to FalkorDB with username, diagram name, and workspace name
        sync_result = await sync_diagram_to_falkordb(diagram, model, workspace, current_user)
        
        if sync_result["success"]:
            logger.info(
                "✅ Diagram successfully synced to FalkorDB",
                diagram_id=str(diagram.id),
                graph_name=sync_result["graph_name"]
            )
        else:
            logger.warning(
                "⚠️  Diagram created but FalkorDB sync failed (non-critical)",
                diagram_id=str(diagram.id),
                error=sync_result.get("error"),
                falkordb_available=sync_result["falkordb_available"]
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
        diagram.updated_by = current_user.id
        
        await db.commit()
        
        logger.info("Diagram deleted", diagram_id=diagram_id, user_id=str(current_user.id))
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting diagram", diagram_id=diagram_id, error=str(e))
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete diagram: {str(e)}"
        )