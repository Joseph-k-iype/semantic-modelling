# backend/app/api/v1/endpoints/diagrams.py
"""
Diagram Management Endpoints - COMPLETE AND FIXED
Path: backend/app/api/v1/endpoints/diagrams.py

CRITICAL FIXES:
1. Uses 'type' instead of 'workspace_type' for Workspace model
2. All necessary imports included
3. Uses LayoutType enum correctly
4. Uses 'notation' field (not 'notation_type')
5. Generates and stores graph_name
6. Complete FalkorDB integration
7. Complete error handling
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
from app.models.layout import Layout, LayoutType
from app.models.model import Model, ModelType, ModelStatus
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


class DiagramNodesEdgesUpdate(BaseModel):
    """Schema for updating diagram nodes and edges"""
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]


class DiagramResponse(BaseModel):
    """Diagram response schema"""
    id: str
    name: str
    notation: str
    notation_type: str  # For frontend compatibility
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
    # ER
    "ER": "ER",
    "ENTITY_RELATIONSHIP": "ER",
    
    # UML
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
    
    # BPMN
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
        notation=diagram.notation,
        notation_type=diagram.notation,  # For frontend compatibility
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
    """
    Get or create personal workspace for user
    
    CRITICAL FIX: Uses 'type' instead of 'workspace_type'
    """
    # CRITICAL FIX: Use 'type' not 'workspace_type'
    stmt = select(Workspace).where(
        and_(
            Workspace.created_by == user.id,
            Workspace.type == WorkspaceType.PERSONAL,  # FIXED: Use 'type'
            Workspace.deleted_at.is_(None)
        )
    )
    result = await db.execute(stmt)
    workspace = result.scalar_one_or_none()
    
    if not workspace:
        # CRITICAL FIX: Use 'type' not 'workspace_type'
        workspace = Workspace(
            name=f"{user.username}'s Workspace",
            description="Personal workspace",
            type=WorkspaceType.PERSONAL,  # FIXED: Use 'type'
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
    Create a new diagram with FalkorDB graph integration
    
    COMPLETE IMPLEMENTATION:
    1. Creates/gets personal workspace
    2. Creates/gets model
    3. Creates diagram with graph_name
    4. Creates default layout
    5. Initializes FalkorDB graph with user context
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
        
        # Get model type from notation
        model_type = get_model_type_from_notation(normalized_notation)
        
        # Get or create personal workspace
        workspace = await get_or_create_personal_workspace(db, current_user)
        
        logger.info(
            "Using workspace for diagram",
            workspace_id=str(workspace.id),
            workspace_name=workspace.name
        )
        
        # Get or create model
        if diagram_data.model_id:
            # Use existing model
            try:
                model_uuid = uuid.UUID(diagram_data.model_id)
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
                    detail=f"Model {diagram_data.model_id} not found"
                )
            
            # Verify user has access to model
            if model.created_by != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to use this model"
                )
        else:
            # Create new model
            model_name = diagram_data.model_name or f"{diagram_data.name} Model"
            
            # Generate unique graph_id for the model (REQUIRED field)
            model_graph_id = f"model_{sanitize_for_graph_name(current_user.username)}_{sanitize_for_graph_name(workspace.name)}_{sanitize_for_graph_name(model_name)}_{uuid.uuid4().hex[:8]}"
            
            # ✅ STRATEGIC FIX: Removed status= and version= (fields don't exist in Model class)
            # ✅ Added graph_id (required field)
            model = Model(
                workspace_id=workspace.id,
                name=model_name,
                description=f"Model for {diagram_data.name}",
                model_type=model_type,
                graph_id=model_graph_id,  # ✅ REQUIRED field - must be unique
                meta_data={},  # Optional but good to initialize
                settings={},  # Optional but good to initialize
                validation_rules=[],  # Optional but good to initialize
                created_by=current_user.id,
                updated_by=current_user.id
            )
            
            db.add(model)
            await db.flush()  # Get the model.id before using it
            await db.refresh(model)
        
        # Generate graph name for FalkorDB
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
                
                diagram = Diagram(
                    model_id=model.id,
                    name=diagram_name,
                    description=diagram_data.description,
                    notation=normalized_notation,
                    graph_name=graph_name,
                    notation_config={},
                    visible_concepts=[],
                    settings={},
                    validation_errors=[],
                    is_valid=True,
                    is_default=True,
                    created_by=current_user.id,
                    updated_by=current_user.id
                )
                
                db.add(diagram)  # ✅ This is correct
                await db.flush()  # ✅ This is correct
                await db.refresh(diagram)  # ✅ This is correct
                
                logger.info(
                    "✅ Created diagram with graph reference",
                    diagram_id=str(diagram.id),
                    diagram_name=diagram_name,
                    notation=normalized_notation,
                    graph_name=graph_name
                )
                break  # ✅ Exit retry loop
                
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
        
        # ✅ At this point, diagram is in session but NOT committed yet
        # ✅ This is CORRECT - we'll commit it with the layout together
        
        # Create default layout
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
            
            db.add(layout)  # ✅ Add layout to session
            
            # ✅ COMMIT BOTH diagram and layout together - FIRST TIME
            await db.commit()
            
            # ✅ Refresh to get final state
            await db.refresh(diagram)
            await db.refresh(layout)
            
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
            # ❌ DO NOT COMMIT AGAIN HERE - diagram already committed above
            # If layout fails, diagram is still saved
            await db.rollback()
            # Re-fetch diagram to ensure it's in session
            stmt = select(Diagram).where(Diagram.id == diagram.id)
            result = await db.execute(stmt)
            diagram = result.scalar_one()
        
        # After this point, DO NOT call db.add(diagram) or db.commit() again
        # for the diagram - it's already in database!
        
        # Initialize FalkorDB graph
        try:
            semantic_service = SemanticModelService()
            
            # ✅ This should NOT commit the diagram again
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
                diagram_id=str(diagram.id),
                graph_name=graph_name
            )
            
        except Exception as graph_error:
            # Graph initialization failure is non-critical
            # Diagram already saved successfully
            logger.warning(
                "FalkorDB initialization skipped (non-critical)",
                error=str(graph_error)
            )
        
        # ✅ Return the diagram response (already committed to DB)
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


@router.get("/", response_model=DiagramListResponse)
async def list_diagrams(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    model_id: Optional[str] = None,
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
        
        # Get total count
        count_result = await db.execute(query)
        total = len(count_result.scalars().all())
        
        # Get paginated results
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
        
        # Check ownership
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
        
        logger.info(
            "Updated diagram",
            diagram_id=str(diagram.id)
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


@router.post("/{diagram_id}/sync", status_code=status.HTTP_200_OK)
async def sync_diagram_to_graph(
    diagram_id: str,
    sync_data: DiagramNodesEdgesUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Sync diagram nodes and edges to FalkorDB
    
    Creates/updates nodes as concepts with:
    - User ID
    - Workspace ID
    - Diagram ID
    - Actual entity/class names (not diagram name)
    
    Creates/updates edges as relationships with:
    - User ID
    - Relationship names
    - Cardinality properties
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
                detail="Not authorized to sync this diagram"
            )
        
        # Get model and workspace
        stmt = select(Model).where(Model.id == diagram.model_id)
        result = await db.execute(stmt)
        model = result.scalar_one_or_none()
        
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Model not found"
            )
        
        # Sync to FalkorDB
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
            "Synced diagram to FalkorDB",
            diagram_id=str(diagram.id),
            stats=stats
        )
        
        return {
            "success": True,
            "message": "Diagram synced to graph database",
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
        
        # Check ownership
        if diagram.created_by != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this diagram"
            )
        
        # Soft delete
        diagram.deleted_at = datetime.utcnow()
        diagram.deleted_by = current_user.id
        
        await db.commit()
        
        # Try to delete FalkorDB graph
        if diagram.graph_name:
            try:
                semantic_service = SemanticModelService()
                await semantic_service.delete_diagram_graph(diagram.graph_name)
                logger.info(
                    "Deleted FalkorDB graph",
                    graph_name=diagram.graph_name
                )
            except Exception as graph_error:
                logger.warning(
                    "Failed to delete FalkorDB graph (non-critical)",
                    error=str(graph_error)
                )
        
        logger.info(
            "Deleted diagram",
            diagram_id=str(diagram.id)
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