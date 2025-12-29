# backend/app/api/v1/endpoints/diagrams.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from pydantic import BaseModel
from datetime import datetime
import uuid

from app.db.session import get_db
from app.models.diagram import Diagram
from app.models.model import Model
from app.models.user import User
from app.core.auth import get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response Models
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


class DiagramResponse(BaseModel):
    id: str
    name: str
    notation_type: str
    model_id: str
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]


@router.post("/", response_model=DiagramResponse)
async def create_diagram(
    diagram_data: DiagramCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new diagram (and model if needed)"""
    try:
        model_id = diagram_data.model_id
        
        # Create model if not provided
        if not model_id:
            model_name = diagram_data.model_name or f"Model for {diagram_data.name}"
            new_model = Model(
                id=str(uuid.uuid4()),
                name=model_name,
                description=f"Auto-generated model for diagram: {diagram_data.name}",
                model_type=diagram_data.notation_type,
                created_by=str(current_user.id),
                created_at=datetime.utcnow()
            )
            db.add(new_model)
            db.flush()
            model_id = new_model.id
            logger.info(f"Created new model: {model_id}")
        
        # Create diagram
        new_diagram = Diagram(
            id=str(uuid.uuid4()),
            model_id=model_id,
            name=diagram_data.name,
            notation_type=diagram_data.notation_type,
            metadata_dict={"nodes": [], "edges": []},
            created_by=str(current_user.id),
            created_at=datetime.utcnow()
        )
        
        db.add(new_diagram)
        db.commit()
        db.refresh(new_diagram)
        
        logger.info(f"Created diagram: {new_diagram.id}")
        
        return DiagramResponse(
            id=new_diagram.id,
            name=new_diagram.name,
            notation_type=new_diagram.notation_type,
            model_id=new_diagram.model_id,
            nodes=[],
            edges=[]
        )
        
    except Exception as e:
        logger.error(f"Error creating diagram: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create diagram: {str(e)}"
        )


@router.get("/{diagram_id}", response_model=DiagramResponse)
async def get_diagram(
    diagram_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get diagram by ID"""
    try:
        diagram = db.query(Diagram).filter(
            Diagram.id == diagram_id,
            Diagram.deleted_at.is_(None)
        ).first()
        
        if not diagram:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Diagram not found"
            )
        
        # Get nodes and edges from metadata
        metadata = diagram.metadata_dict or {}
        nodes = metadata.get('nodes', [])
        edges = metadata.get('edges', [])
        
        return DiagramResponse(
            id=diagram.id,
            name=diagram.name,
            notation_type=diagram.notation_type,
            model_id=diagram.model_id,
            nodes=nodes,
            edges=edges
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting diagram: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get diagram"
        )


@router.get("/models/{model_id}/diagrams", response_model=List[DiagramResponse])
async def list_diagrams_by_model(
    model_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all diagrams for a model"""
    try:
        diagrams = db.query(Diagram).filter(
            Diagram.model_id == model_id,
            Diagram.deleted_at.is_(None)
        ).all()
        
        return [
            DiagramResponse(
                id=d.id,
                name=d.name,
                notation_type=d.notation_type,
                model_id=d.model_id,
                nodes=d.metadata_dict.get('nodes', []),
                edges=d.metadata_dict.get('edges', [])
            )
            for d in diagrams
        ]
        
    except Exception as e:
        logger.error(f"Error listing diagrams: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list diagrams"
        )


@router.get("/models/{model_id}/diagrams/{diagram_id}", response_model=DiagramResponse)
async def get_diagram_by_model(
    model_id: str,
    diagram_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get specific diagram in a model"""
    try:
        diagram = db.query(Diagram).filter(
            Diagram.id == diagram_id,
            Diagram.model_id == model_id,
            Diagram.deleted_at.is_(None)
        ).first()
        
        if not diagram:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Diagram not found"
            )
        
        metadata = diagram.metadata_dict or {}
        
        return DiagramResponse(
            id=diagram.id,
            name=diagram.name,
            notation_type=diagram.notation_type,
            model_id=diagram.model_id,
            nodes=metadata.get('nodes', []),
            edges=metadata.get('edges', [])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting diagram: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get diagram"
        )


@router.put("/models/{model_id}/diagrams/{diagram_id}/nodes/{node_id}")
async def update_node(
    model_id: str,
    diagram_id: str,
    node_id: str,
    node_data: NodeDataRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update or create a node"""
    try:
        diagram = db.query(Diagram).filter(
            Diagram.id == diagram_id,
            Diagram.model_id == model_id,
            Diagram.deleted_at.is_(None)
        ).first()
        
        if not diagram:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Diagram not found"
            )
        
        # Get existing metadata
        metadata = diagram.metadata_dict or {}
        nodes = metadata.get('nodes', [])
        
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
        metadata['nodes'] = nodes
        diagram.metadata_dict = metadata
        diagram.updated_by = str(current_user.id)
        diagram.updated_at = datetime.utcnow()
        
        db.commit()
        
        logger.info(f"Updated node {node_id} in diagram {diagram_id}")
        
        return {
            'success': True,
            'node_id': node_id,
            'message': 'Node updated successfully'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating node: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update node: {str(e)}"
        )


@router.put("/models/{model_id}/diagrams/{diagram_id}/edges/{edge_id}")
async def update_edge(
    model_id: str,
    diagram_id: str,
    edge_id: str,
    edge_data: EdgeDataRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update or create an edge"""
    try:
        diagram = db.query(Diagram).filter(
            Diagram.id == diagram_id,
            Diagram.model_id == model_id,
            Diagram.deleted_at.is_(None)
        ).first()
        
        if not diagram:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Diagram not found"
            )
        
        # Get existing metadata
        metadata = diagram.metadata_dict or {}
        edges = metadata.get('edges', [])
        
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
        metadata['edges'] = edges
        diagram.metadata_dict = metadata
        diagram.updated_by = str(current_user.id)
        diagram.updated_at = datetime.utcnow()
        
        db.commit()
        
        logger.info(f"Updated edge {edge_id} in diagram {diagram_id}")
        
        return {
            'success': True,
            'edge_id': edge_id,
            'message': 'Edge updated successfully'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating edge: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update edge: {str(e)}"
        )


@router.delete("/{diagram_id}")
async def delete_diagram(
    diagram_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Soft delete a diagram"""
    try:
        diagram = db.query(Diagram).filter(
            Diagram.id == diagram_id,
            Diagram.deleted_at.is_(None)
        ).first()
        
        if not diagram:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Diagram not found"
            )
        
        # Soft delete
        diagram.deleted_at = datetime.utcnow()
        diagram.updated_by = str(current_user.id)
        diagram.updated_at = datetime.utcnow()
        
        db.commit()
        
        logger.info(f"Deleted diagram {diagram_id}")
        
        return {
            'success': True,
            'message': 'Diagram deleted successfully'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting diagram: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete diagram"
        )