# backend/app/services/semantic_model_service.py
"""
Semantic Model Service - COMPLETE WORKING VERSION
Path: backend/app/services/semantic_model_service.py
"""
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog

logger = structlog.get_logger(__name__)


class SemanticModelService:
    """Service for managing semantic models in FalkorDB"""
    
    def __init__(self):
        try:
            from app.graph.client import get_graph_client
            self.graph_client = get_graph_client()
            
            if self.graph_client.is_connected():
                logger.info("Semantic model service initialized with FalkorDB")
            else:
                logger.warning("Semantic model service initialized but FalkorDB not connected")
        except Exception as e:
            logger.error("Failed to initialize graph client", error=str(e))
            self.graph_client = None
    
    def _get_graph_name(self, user_id: str, model_id: str) -> str:
        """Generate unique graph name"""
        safe_user_id = str(user_id).replace("-", "_")
        safe_model_id = str(model_id).replace("-", "_")
        return f"user_{safe_user_id}_model_{safe_model_id}"
    
    async def sync_diagram_to_graph(
        self,
        db: AsyncSession,
        diagram_id: str,
        user_id: str,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Sync diagram data to semantic graph"""
        stats = {
            "concepts_created": 0,
            "concepts_updated": 0,
            "relationships_created": 0,
            "errors": [],
            "falkordb_available": False,
            "falkordb_connected": False
        }
        
        if not self.graph_client:
            logger.warning("FalkorDB client not available, skipping sync")
            stats["errors"].append("FalkorDB client not initialized")
            return stats
        
        if not self.graph_client.is_connected():
            logger.warning("FalkorDB not connected, attempting reconnect")
            if not self.graph_client.connect():
                logger.error("Failed to reconnect to FalkorDB")
                stats["errors"].append("FalkorDB connection failed")
                return stats
        
        try:
            from app.models.diagram import Diagram
            
            result = await db.execute(
                select(Diagram).where(Diagram.id == diagram_id)
            )
            diagram = result.scalar_one_or_none()
            
            if not diagram:
                error_msg = f"Diagram {diagram_id} not found"
                logger.error(error_msg)
                stats["errors"].append(error_msg)
                return stats
            
            graph_name = self._get_graph_name(user_id, str(diagram.model_id))
            
            stats["falkordb_available"] = True
            stats["falkordb_connected"] = True
            
            # Process nodes
            for node in nodes:
                try:
                    node_id = node.get("id")
                    if not node_id:
                        continue
                    
                    created = self._sync_node_to_concept(
                        graph_name,
                        node,
                        diagram.notation
                    )
                    
                    if created:
                        stats["concepts_created"] += 1
                    else:
                        stats["concepts_updated"] += 1
                        
                except Exception as e:
                    error_msg = f"Failed to sync node {node.get('id')}: {str(e)}"
                    logger.error(error_msg)
                    stats["errors"].append(error_msg)
            
            # Process edges
            for edge in edges:
                try:
                    edge_id = edge.get("id")
                    if not edge_id:
                        continue
                    
                    success = self._sync_edge_to_relationship(
                        graph_name,
                        edge,
                        diagram.notation
                    )
                    
                    if success:
                        stats["relationships_created"] += 1
                    
                except Exception as e:
                    error_msg = f"Failed to sync edge {edge.get('id')}: {str(e)}"
                    logger.error(error_msg)
                    stats["errors"].append(error_msg)
            
            logger.info(
                "Diagram synced to graph",
                diagram_id=diagram_id,
                stats=stats
            )
            
        except Exception as e:
            error_msg = f"Failed to sync diagram: {str(e)}"
            logger.error(error_msg)
            stats["errors"].append(error_msg)
        
        return stats
    
    def _sync_node_to_concept(
        self,
        graph_name: str,
        node: Dict[str, Any],
        diagram_type: str
    ) -> bool:
        """Sync node to concept - returns True if created, False if updated"""
        if not self.graph_client or not self.graph_client.is_connected():
            return False
        
        node_id = node.get("id")
        node_type = node.get("type")
        node_data = node.get("data", {})
        
        properties = {
            "name": node_data.get("label", node_data.get("name", "Unnamed")),
            "diagram_type": diagram_type,
            "node_type": node_type,
            "position_x": node.get("position", {}).get("x", 0),
            "position_y": node.get("position", {}).get("y", 0)
        }
        
        try:
            # Check if exists
            existing = self.graph_client.execute_query(
                graph_name,
                "MATCH (c:Concept {id: $id}) RETURN c",
                {"id": node_id}
            )
            
            if existing and len(existing) > 0:
                self.graph_client.update_concept(graph_name, node_id, properties)
                return False
            else:
                self.graph_client.create_concept(
                    graph_name,
                    node_id,
                    node_type or "Concept",
                    properties
                )
                return True
                
        except Exception as e:
            logger.error("Failed to sync node", node_id=node_id, error=str(e))
            raise
    
    def _sync_edge_to_relationship(
        self,
        graph_name: str,
        edge: Dict[str, Any],
        diagram_type: str
    ) -> bool:
        """Sync edge to relationship"""
        if not self.graph_client or not self.graph_client.is_connected():
            return False
        
        edge_id = edge.get("id")
        source = edge.get("source")
        target = edge.get("target")
        edge_type = edge.get("type", "RELATED_TO")
        edge_data = edge.get("data", {})
        
        properties = {
            "id": edge_id,
            "label": edge_data.get("label", ""),
            "diagram_type": diagram_type,
            "edge_type": edge_type
        }
        
        try:
            return self.graph_client.create_relationship(
                graph_name,
                source,
                target,
                edge_type,
                properties
            )
        except Exception as e:
            logger.error("Failed to sync edge", edge_id=edge_id, error=str(e))
            return False