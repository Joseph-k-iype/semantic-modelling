# backend/app/api/v1/endpoints/diagrams.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from app.db.session import get_db
from app.models.diagram import Diagram
from app.models.user import User
from app.core.auth import get_current_user
from app.services.graph_sync_service import graph_sync_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic models for request/response
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


class DiagramResponse(BaseModel):
    id: str
    name: str
    notation: str
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]


@router.get("/models/{model_id}/diagrams/{diagram_id}", response_model=DiagramResponse)
async def get_diagram(
    model_id: str,
    diagram_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get diagram with nodes and edges"""
    try:
        # Get diagram from database
        diagram = db.query(Diagram).filter(
            Diagram.id == diagram_id,
            Diagram.model_id == model_id
        ).first()
        
        if not diagram:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Diagram not found"
            )
        
        # Get nodes and edges from diagram metadata
        nodes = diagram.metadata_dict.get('nodes', [])
        edges = diagram.metadata_dict.get('edges', [])
        
        return DiagramResponse(
            id=diagram.id,
            name=diagram.name,
            notation=diagram.notation_type,
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


@router.put("/models/{model_id}/diagrams/{diagram_id}/nodes/{node_id}")
async def update_node(
    model_id: str,
    diagram_id: str,
    node_id: str,
    node_data: NodeDataRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update or create a node and sync to graph database"""
    try:
        # Get diagram
        diagram = db.query(Diagram).filter(
            Diagram.id == diagram_id,
            Diagram.model_id == model_id
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
        node_exists = False
        for i, node in enumerate(nodes):
            if node['id'] == node_id:
                nodes[i] = {
                    'id': node_id,
                    'type': node_data.type,
                    'position': node_data.position,
                    'data': node_data.data
                }
                node_exists = True
                break
        
        if not node_exists:
            nodes.append({
                'id': node_id,
                'type': node_data.type,
                'position': node_data.position,
                'data': node_data.data
            })
        
        # Update diagram metadata
        metadata['nodes'] = nodes
        diagram.metadata_dict = metadata
        db.commit()
        
        # Sync to graph database based on notation
        sync_result = None
        if node_data.notation == 'er':
            sync_result = await graph_sync_service.sync_er_entity(
                model_id=model_id,
                diagram_id=diagram_id,
                node_id=node_id,
                node_data=node_data.data
            )
        elif node_data.notation in ['uml-class', 'uml-interaction']:
            sync_result = await graph_sync_service.sync_uml_class(
                model_id=model_id,
                diagram_id=diagram_id,
                node_id=node_id,
                node_data=node_data.data
            )
        elif node_data.notation == 'bpmn':
            # Determine BPMN element type from node type
            element_type_map = {
                'taskNode': 'task',
                'eventNode': 'event',
                'gatewayNode': 'gateway',
                'poolNode': 'pool'
            }
            element_type = element_type_map.get(node_data.type, 'task')
            
            sync_result = await graph_sync_service.sync_bpmn_element(
                model_id=model_id,
                diagram_id=diagram_id,
                node_id=node_id,
                node_data=node_data.data,
                element_type=element_type
            )
        
        return {
            'success': True,
            'node_id': node_id,
            'graph_sync': sync_result,
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
    """Update or create an edge and sync to graph database"""
    try:
        # Get diagram
        diagram = db.query(Diagram).filter(
            Diagram.id == diagram_id,
            Diagram.model_id == model_id
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
        edge_exists = False
        edge_dict = {
            'id': edge_id,
            'source': edge_data.source,
            'target': edge_data.target,
            'type': edge_data.type,
            'data': edge_data.data
        }
        
        for i, edge in enumerate(edges):
            if edge['id'] == edge_id:
                edges[i] = edge_dict
                edge_exists = True
                break
        
        if not edge_exists:
            edges.append(edge_dict)
        
        # Update diagram metadata
        metadata['edges'] = edges
        diagram.metadata_dict = metadata
        db.commit()
        
        # Sync to graph database based on notation
        sync_result = None
        if edge_data.notation == 'er':
            sync_result = await graph_sync_service.sync_er_relationship(
                model_id=model_id,
                diagram_id=diagram_id,
                edge_id=edge_id,
                edge_data=edge_dict
            )
        elif edge_data.notation in ['uml-class', 'uml-interaction']:
            sync_result = await graph_sync_service.sync_uml_relationship(
                model_id=model_id,
                diagram_id=diagram_id,
                edge_id=edge_id,
                edge_data=edge_dict
            )
        elif edge_data.notation == 'bpmn':
            sync_result = await graph_sync_service.sync_bpmn_flow(
                model_id=model_id,
                diagram_id=diagram_id,
                edge_id=edge_id,
                edge_data=edge_dict
            )
        
        return {
            'success': True,
            'edge_id': edge_id,
            'graph_sync': sync_result,
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


@router.get("/models/{model_id}/diagrams/{diagram_id}/lineage/{element_id}")
async def get_element_lineage(
    model_id: str,
    diagram_id: str,
    element_id: str,
    depth: int = 3,
    current_user: User = Depends(get_current_user)
):
    """Get lineage information for a diagram element"""
    try:
        full_element_id = f"{model_id}:{element_id}"
        lineage = await graph_sync_service.get_lineage(full_element_id, depth)
        
        return {
            'success': True,
            'element_id': element_id,
            'lineage': lineage
        }
        
    except Exception as e:
        logger.error(f"Error getting lineage: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get lineage"
        )


@router.get("/models/{model_id}/diagrams/{diagram_id}/impact/{element_id}")
async def get_element_impact(
    model_id: str,
    diagram_id: str,
    element_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get impact analysis for a diagram element"""
    try:
        full_element_id = f"{model_id}:{element_id}"
        impact = await graph_sync_service.get_impact_analysis(full_element_id)
        
        return {
            'success': True,
            'element_id': element_id,
            'impact_analysis': impact
        }
        
    except Exception as e:
        logger.error(f"Error getting impact analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get impact analysis"
        )


@router.delete("/models/{model_id}/diagrams/{diagram_id}/nodes/{node_id}")
async def delete_node(
    model_id: str,
    diagram_id: str,
    node_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a node from diagram and graph database"""
    try:
        # Get diagram
        diagram = db.query(Diagram).filter(
            Diagram.id == diagram_id,
            Diagram.model_id == model_id
        ).first()
        
        if not diagram:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Diagram not found"
            )
        
        # Remove node from metadata
        metadata = diagram.metadata_dict or {}
        nodes = metadata.get('nodes', [])
        metadata['nodes'] = [n for n in nodes if n['id'] != node_id]
        
        diagram.metadata_dict = metadata
        db.commit()
        
        # Delete from graph database
        delete_query = """
        MATCH (n {id: $element_id})
        DETACH DELETE n
        """
        
        await graph_sync_service.graph.execute_query(
            delete_query,
            {'element_id': f"{model_id}:{node_id}"}
        )
        
        return {
            'success': True,
            'message': 'Node deleted successfully'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting node: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete node"
        )


@router.delete("/models/{model_id}/diagrams/{diagram_id}/edges/{edge_id}")
async def delete_edge(
    model_id: str,
    diagram_id: str,
    edge_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an edge from diagram and graph database"""
    try:
        # Get diagram
        diagram = db.query(Diagram).filter(
            Diagram.id == diagram_id,
            Diagram.model_id == model_id
        ).first()
        
        if not diagram:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Diagram not found"
            )
        
        # Remove edge from metadata
        metadata = diagram.metadata_dict or {}
        edges = metadata.get('edges', [])
        metadata['edges'] = [e for e in edges if e['id'] != edge_id]
        
        diagram.metadata_dict = metadata
        db.commit()
        
        # Delete from graph database
        delete_query = """
        MATCH ()-[r {id: $element_id}]-()
        DELETE r
        """
        
        await graph_sync_service.graph.execute_query(
            delete_query,
            {'element_id': f"{model_id}:{edge_id}"}
        )
        
        return {
            'success': True,
            'message': 'Edge deleted successfully'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting edge: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete edge"
        )