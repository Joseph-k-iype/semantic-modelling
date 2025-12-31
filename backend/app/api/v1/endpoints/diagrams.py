# backend/app/api/v1/endpoints/diagrams.py
"""
Diagram management endpoints - COMPLETE AND FIXED
Path: backend/app/api/v1/endpoints/diagrams.py
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any
from pydantic import BaseModel
from datetime import datetime
import uuid
import structlog

from app.db.session import get_db
from app.models.diagram import Diagram
from app.models.model import Model
from app.models.workspace import Workspace, WorkspaceType
from app.models.user import User
from app.core.auth import get_current_user

logger = structlog.get_logger(__name__)

router = APIRouter()


# ============================================================================
# REQUEST/RESPONSE SCHEMAS
# ============================================================================

class NodeDataRequest(BaseModel):
    type: str
    position: Dict[str, float]
    data: Dict[str, Any]
    notation: str


class EdgeDataRequest(BaseModel):
    source: str
    target: str
    type: str
    data: Dict[str, Any]
    notation: str


class DiagramCreateRequest(BaseModel):
    name: str
    notation_type: str  # er, uml_class, bpmn, etc.
    model_id: str | None = None  # Optional - will create new model if not provided
    model_name: str | None = None
    workspace_id: str | None = None  # Optional - will use personal workspace if not provided


class DiagramResponse(BaseModel):
    id: str
    name: str
    notation_type: str
    model_id: str
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def get_or_create_personal_workspace(
    db: AsyncSession,
    user: User
) -> Workspace:
    """
    Get user's personal workspace or create it if it doesn't exist
    
    CRITICAL FIX: Now that we use native_enum=False in the model,
    we can compare directly with the enum member and SQLAlchemy
    will use the value automatically
    """
    # Try to find existing personal workspace
    # ✅ With native_enum=False, we can now use the enum directly
    result = await db.execute(
        select(Workspace).where(
            Workspace.created_by == user.id,
            Workspace.type == WorkspaceType.PERSONAL  # ✅ SQLAlchemy converts to "personal"
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
        type=WorkspaceType.PERSONAL,  # ✅ SQLAlchemy stores as "personal"
        created_by=user.id,
        settings={},
        is_active=True
    )
    db.add(workspace)
    await db.flush()
    
    logger.info("Created personal workspace", user_id=str(user.id), workspace_id=str(workspace.id))
    
    return workspace


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/", response_model=DiagramResponse)
async def create_diagram(
    diagram_data: DiagramCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new diagram (and model if needed)
    
    FIXED: 
    - Workspace enum now properly configured to use values
    - Can use enum members directly in comparisons
    """
    try:
        model_id = diagram_data.model_id
        
        # Create model if not provided
        if not model_id:
            # Get workspace_id
            if diagram_data.workspace_id:
                workspace_id = uuid.UUID(diagram_data.workspace_id)
            else:
                # Get or create personal workspace
                workspace = await get_or_create_personal_workspace(db, current_user)
                workspace_id = workspace.id
            
            model_name = diagram_data.model_name or f"Model for {diagram_data.name}"
            
            # Create new model with required workspace_id
            new_model = Model(
                name=model_name,
                description=f"Auto-generated model for diagram: {diagram_data.name}",
                type=diagram_data.notation_type,
                workspace_id=workspace_id,  # ✅ REQUIRED field
                created_by=current_user.id,
            )
            db.add(new_model)
            await db.flush()
            model_id = new_model.id
            logger.info("Created new model", model_id=str(model_id), workspace_id=str(workspace_id))
        
        # Create diagram
        new_diagram = Diagram(
            model_id=model_id,
            name=diagram_data.name,
            notation_type=diagram_data.notation_type,
            data={"nodes": [], "edges": []},
            created_by=current_user.id,
        )
        
        db.add(new_diagram)
        await db.commit()
        await db.refresh(new_diagram)
        
        logger.info("Created diagram", diagram_id=str(new_diagram.id))
        
        return DiagramResponse(
            id=str(new_diagram.id),
            name=new_diagram.name,
            notation_type=new_diagram.notation_type,
            model_id=str(new_diagram.model_id),
            nodes=[],
            edges=[]
        )
        
    except Exception as e:
        logger.error("Error creating diagram", error=str(e), error_type=type(e).__name__)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create diagram: {str(e)}"
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
        
        # Check if diagram is soft-deleted (if deleted_at exists)
        if hasattr(diagram, 'deleted_at') and diagram.deleted_at is not None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Diagram not found"
            )
        
        # Get nodes and edges from data
        data = diagram.data or {}
        nodes = data.get('nodes', [])
        edges = data.get('edges', [])
        
        return DiagramResponse(
            id=str(diagram.id),
            name=diagram.name,
            notation_type=diagram.notation_type,
            model_id=str(diagram.model_id),
            nodes=nodes,
            edges=edges
        )
        
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
            detail="Failed to get diagram"
        )


@router.get("/", response_model=List[DiagramResponse])
async def list_diagrams(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all diagrams for the current user"""
    result = await db.execute(
        select(Diagram)
        .where(Diagram.created_by == current_user.id)
        .offset(skip)
        .limit(limit)
        .order_by(Diagram.created_at.desc())
    )
    diagrams = result.scalars().all()
    
    logger.info("Diagrams listed", count=len(diagrams), user_id=str(current_user.id))
    
    return [
        DiagramResponse(
            id=str(d.id),
            name=d.name,
            notation_type=d.notation_type,
            model_id=str(d.model_id),
            nodes=d.data.get('nodes', []) if d.data else [],
            edges=d.data.get('edges', []) if d.data else []
        )
        for d in diagrams
    ]


@router.get("/models/{model_id}/diagrams", response_model=List[DiagramResponse])
async def list_diagrams_by_model(
    model_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all diagrams for a model"""
    try:
        model_uuid = uuid.UUID(model_id)
        
        result = await db.execute(
            select(Diagram).where(Diagram.model_id == model_uuid)
        )
        diagrams = result.scalars().all()
        
        # Filter out soft-deleted diagrams if column exists
        diagrams = [d for d in diagrams if not (hasattr(d, 'deleted_at') and d.deleted_at)]
        
        return [
            DiagramResponse(
                id=str(d.id),
                name=d.name,
                notation_type=d.notation_type,
                model_id=str(d.model_id),
                nodes=d.data.get('nodes', []) if d.data else [],
                edges=d.data.get('edges', []) if d.data else []
            )
            for d in diagrams
        ]
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid model ID format"
        )
    except Exception as e:
        logger.error("Error listing diagrams", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list diagrams"
        )


@router.put("/{diagram_id}", response_model=DiagramResponse)
async def update_diagram(
    diagram_id: str,
    diagram_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update diagram"""
    try:
        diagram_uuid = uuid.UUID(diagram_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid diagram ID format"
        )
    
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
    if "name" in diagram_data:
        diagram.name = diagram_data["name"]
    if "data" in diagram_data:
        diagram.data = diagram_data["data"]
    
    await db.commit()
    await db.refresh(diagram)
    
    logger.info("Diagram updated", diagram_id=diagram_id)
    
    return DiagramResponse(
        id=str(diagram.id),
        name=diagram.name,
        notation_type=diagram.notation_type,
        model_id=str(diagram.model_id),
        nodes=diagram.data.get("nodes", []),
        edges=diagram.data.get("edges", [])
    )


@router.put("/{diagram_id}/nodes/{node_id}")
async def update_node(
    diagram_id: str,
    node_id: str,
    node_data: NodeDataRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update or create a node"""
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
        
        # Get existing data
        data = diagram.data or {}
        nodes = data.get('nodes', [])
        
        # Update or add node
        node_dict = {
            'id': node_id,
            'type': node_data.type,
            'position': node_data.position,
            'data': node_data.data
        }
        
        node_exists = False
        for i, node in enumerate(nodes):
            if node['id'] == node_id:
                nodes[i] = node_dict
                node_exists = True
                break
        
        if not node_exists:
            nodes.append(node_dict)
        
        # Update diagram
        data['nodes'] = nodes
        diagram.data = data
        diagram.updated_by = current_user.id
        diagram.updated_at = datetime.utcnow()
        
        await db.commit()
        
        logger.info("Updated node", diagram_id=diagram_id, node_id=node_id)
        
        return {
            'success': True,
            'node_id': node_id,
            'message': 'Node updated successfully'
        }
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ID format"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating node", error=str(e))
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update node: {str(e)}"
        )


@router.put("/{diagram_id}/edges/{edge_id}")
async def update_edge(
    diagram_id: str,
    edge_id: str,
    edge_data: EdgeDataRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update or create an edge"""
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
        
        # Get existing data
        data = diagram.data or {}
        edges = data.get('edges', [])
        
        # Update or add edge
        edge_dict = {
            'id': edge_id,
            'source': edge_data.source,
            'target': edge_data.target,
            'type': edge_data.type,
            'data': edge_data.data
        }
        
        edge_exists = False
        for i, edge in enumerate(edges):
            if edge['id'] == edge_id:
                edges[i] = edge_dict
                edge_exists = True
                break
        
        if not edge_exists:
            edges.append(edge_dict)
        
        # Update diagram
        data['edges'] = edges
        diagram.data = data
        diagram.updated_by = current_user.id
        diagram.updated_at = datetime.utcnow()
        
        await db.commit()
        
        logger.info("Updated edge", diagram_id=diagram_id, edge_id=edge_id)
        
        return {
            'success': True,
            'edge_id': edge_id,
            'message': 'Edge updated successfully'
        }
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ID format"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating edge", error=str(e))
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update edge: {str(e)}"
        )


@router.delete("/{diagram_id}")
async def delete_diagram(
    diagram_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a diagram (soft delete if column exists, hard delete otherwise)"""
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
        
        # Check if soft delete is supported
        if hasattr(diagram, 'deleted_at'):
            # Soft delete
            diagram.deleted_at = datetime.utcnow()
        else:
            # Hard delete
            await db.delete(diagram)
        
        await db.commit()
        
        logger.info("Deleted diagram", diagram_id=diagram_id)
        
        return {
            'success': True,
            'message': 'Diagram deleted successfully'
        }
        
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