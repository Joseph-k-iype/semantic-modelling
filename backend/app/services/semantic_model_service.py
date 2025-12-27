# backend/app/services/semantic_model_service.py
"""
Semantic Model Service - FIXED
Manages the semantic graph layer and syncs with diagram data
"""
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.graph.client import get_graph_client
from app.models.model import Model
from app.models.diagram import Diagram
import structlog

logger = structlog.get_logger()


class SemanticModelService:
    """Service for managing semantic models in FalkorDB"""
    
    def __init__(self):
        try:
            self.graph_client = get_graph_client()
            if self.graph_client.is_connected():
                logger.info("Semantic model service initialized with FalkorDB")
            else:
                logger.warning("Semantic model service initialized but FalkorDB is not connected")
        except Exception as e:
            logger.error("Failed to initialize graph client", error=str(e))
            self.graph_client = None
    
    def _get_graph_name(self, user_id: str, model_id: str) -> str:
        """Generate unique graph name for user and model"""
        # Sanitize IDs to be valid graph names
        safe_user_id = user_id.replace("-", "_")
        safe_model_id = model_id.replace("-", "_")
        return f"user_{safe_user_id}_model_{safe_model_id}"
    
    async def sync_diagram_to_graph(
        self,
        db: AsyncSession,
        diagram_id: str,
        user_id: str,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Sync diagram data to semantic graph
        
        Args:
            db: Database session
            diagram_id: Diagram ID
            user_id: User ID
            nodes: List of diagram nodes
            edges: List of diagram edges
            
        Returns:
            Sync result with statistics
        """
        stats = {
            "concepts_created": 0,
            "concepts_updated": 0,
            "relationships_created": 0,
            "errors": [],
            "falkordb_available": False,
            "falkordb_connected": False
        }
        
        # Check if graph client is available and connected
        if not self.graph_client:
            logger.warning("FalkorDB client not available, skipping graph sync")
            stats["errors"].append("FalkorDB client not initialized")
            return stats
        
        if not self.graph_client.is_connected():
            logger.warning("FalkorDB client not connected, attempting to reconnect")
            if not self.graph_client.connect():
                logger.error("Failed to reconnect to FalkorDB, skipping graph sync")
                stats["errors"].append("FalkorDB connection failed")
                return stats
        
        try:
            # Get diagram and model
            from app.repositories.diagram_repository import DiagramRepository
            diagram_repo = DiagramRepository(db)
            diagram = await diagram_repo.get(diagram_id)
            
            if not diagram:
                error_msg = f"Diagram {diagram_id} not found"
                logger.error(error_msg)
                stats["errors"].append(error_msg)
                return stats
            
            graph_name = self._get_graph_name(user_id, diagram.model_id)
            logger.info(
                "Syncing diagram to graph",
                diagram_id=diagram_id,
                graph_name=graph_name,
                node_count=len(nodes),
                edge_count=len(edges)
            )
            
            stats["falkordb_available"] = True
            stats["falkordb_connected"] = True
            
            # Process nodes -> concepts
            for idx, node in enumerate(nodes):
                try:
                    node_id = node.get("id")
                    if not node_id:
                        logger.warning(f"Node {idx} missing ID, skipping")
                        continue
                    
                    created = await self._sync_node_to_concept(graph_name, node, diagram.type)
                    
                    if created:
                        stats["concepts_created"] += 1
                    else:
                        stats["concepts_updated"] += 1
                        
                except Exception as e:
                    error_msg = f"Failed to sync node {node.get('id', idx)}: {str(e)}"
                    logger.error(error_msg, exc_info=True)
                    stats["errors"].append(error_msg)
            
            # Process edges -> relationships
            for idx, edge in enumerate(edges):
                try:
                    edge_id = edge.get("id")
                    if not edge_id:
                        logger.warning(f"Edge {idx} missing ID, skipping")
                        continue
                    
                    success = await self._sync_edge_to_relationship(graph_name, edge, diagram.type)
                    if success:
                        stats["relationships_created"] += 1
                    
                except Exception as e:
                    error_msg = f"Failed to sync edge {edge.get('id', idx)}: {str(e)}"
                    logger.error(error_msg, exc_info=True)
                    stats["errors"].append(error_msg)
            
            logger.info(
                "Diagram synced to graph successfully",
                diagram_id=diagram_id,
                graph_name=graph_name,
                stats=stats
            )
            
        except Exception as e:
            error_msg = f"Failed to sync diagram to graph: {str(e)}"
            logger.error(error_msg, exc_info=True)
            stats["errors"].append(error_msg)
            stats["falkordb_available"] = False
        
        return stats
    
    async def _sync_node_to_concept(
        self,
        graph_name: str,
        node: Dict[str, Any],
        diagram_type: str
    ) -> bool:
        """
        Sync a diagram node to a semantic concept
        
        Returns:
            True if concept was created (new), False if updated (existing)
        """
        if not self.graph_client or not self.graph_client.is_connected():
            return False
        
        node_id = node.get("id")
        node_type = node.get("type")
        node_data = node.get("data", {})
        
        # Determine concept type based on diagram type and node type
        concept_type = self._get_concept_type(diagram_type, node_type)
        
        # Extract properties based on node type
        properties = self._extract_node_properties(node_type, node_data)
        properties["diagram_type"] = diagram_type
        properties["node_type"] = node_type
        properties["position_x"] = node.get("position", {}).get("x", 0)
        properties["position_y"] = node.get("position", {}).get("y", 0)
        
        try:
            # Check if concept exists
            existing = self.graph_client.execute_query(
                graph_name,
                "MATCH (c:Concept {id: $id}) RETURN c",
                {"id": node_id}
            )
            
            if existing and len(existing) > 0:
                # Update existing concept
                logger.debug(f"Updating existing concept: {node_id}")
                self.graph_client.update_concept(graph_name, node_id, properties)
                return False  # Updated
            else:
                # Create new concept
                logger.debug(f"Creating new concept: {node_id} type: {concept_type}")
                self.graph_client.create_concept(graph_name, node_id, concept_type, properties)
                return True  # Created
                
        except Exception as e:
            logger.error(f"Failed to sync node to concept", node_id=node_id, error=str(e))
            raise
    
    async def _sync_edge_to_relationship(
        self,
        graph_name: str,
        edge: Dict[str, Any],
        diagram_type: str
    ) -> bool:
        """Sync a diagram edge to a semantic relationship"""
        if not self.graph_client or not self.graph_client.is_connected():
            return False
        
        edge_id = edge.get("id")
        source = edge.get("source")
        target = edge.get("target")
        edge_type = edge.get("type", "RELATED_TO")
        edge_data = edge.get("data", {})
        
        # Determine relationship type
        rel_type = self._get_relationship_type(diagram_type, edge_type)
        
        # Extract properties
        properties = {
            "id": edge_id,
            "label": edge_data.get("label", ""),
            "diagram_type": diagram_type,
            "edge_type": edge_type
        }
        
        # Add cardinality for ER diagrams
        if diagram_type == "ER" and "relationship" in edge_data:
            relationship = edge_data["relationship"]
            properties["cardinality_source"] = relationship.get("cardinalitySource", "")
            properties["cardinality_target"] = relationship.get("cardinalityTarget", "")
            properties["is_identifying"] = relationship.get("isIdentifying", False)
        
        try:
            # Create relationship (Cypher will handle duplicates)
            success = self.graph_client.create_relationship(
                graph_name,
                source,
                target,
                rel_type,
                properties
            )
            return success
            
        except Exception as e:
            logger.error(f"Failed to sync edge to relationship", edge_id=edge_id, error=str(e))
            raise
    
    def _get_concept_type(self, diagram_type: str, node_type: str) -> str:
        """Determine concept type from diagram type and node type"""
        # ER diagrams
        if diagram_type == "ER":
            if "ENTITY" in node_type:
                return "Entity"
            elif "RELATIONSHIP" in node_type:
                return "Relationship"
        
        # UML diagrams
        elif diagram_type.startswith("UML"):
            if "CLASS" in node_type:
                return "Class"
            elif "INTERFACE" in node_type:
                return "Interface"
            elif "PACKAGE" in node_type:
                return "Package"
            elif "COMPONENT" in node_type:
                return "Component"
            elif "STATE" in node_type:
                return "State"
            elif "ACTIVITY" in node_type:
                return "Activity"
        
        # BPMN diagrams
        elif diagram_type == "BPMN":
            if "TASK" in node_type:
                return "Task"
            elif "EVENT" in node_type:
                return "Event"
            elif "GATEWAY" in node_type:
                return "Gateway"
            elif "POOL" in node_type:
                return "Pool"
        
        return "Concept"
    
    def _get_relationship_type(self, diagram_type: str, edge_type: str) -> str:
        """Determine relationship type from diagram and edge type"""
        # ER relationships
        if diagram_type == "ER":
            return "RELATES_TO"
        
        # UML relationships
        elif diagram_type.startswith("UML"):
            if "ASSOCIATION" in edge_type:
                return "ASSOCIATES_WITH"
            elif "GENERALIZATION" in edge_type:
                return "INHERITS_FROM"
            elif "DEPENDENCY" in edge_type:
                return "DEPENDS_ON"
            elif "AGGREGATION" in edge_type:
                return "AGGREGATES"
            elif "COMPOSITION" in edge_type:
                return "COMPOSES"
        
        # BPMN flows
        elif diagram_type == "BPMN":
            if "SEQUENCE" in edge_type:
                return "FLOWS_TO"
            elif "MESSAGE" in edge_type:
                return "SENDS_MESSAGE_TO"
        
        return "RELATED_TO"
    
    def _extract_node_properties(self, node_type: str, node_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract properties from node data based on node type"""
        properties = {
            "label": node_data.get("label", ""),
            "description": node_data.get("description", "")
        }
        
        # ER Entity
        if "entity" in node_data and node_data["entity"]:
            entity = node_data["entity"]
            properties["name"] = entity.get("name", "")
            properties["is_weak"] = entity.get("isWeak", False)
            properties["attributes_count"] = len(entity.get("attributes", []))
        
        # UML Class
        elif "class" in node_data and node_data["class"]:
            uml_class = node_data["class"]
            properties["name"] = uml_class.get("name", "")
            properties["is_abstract"] = uml_class.get("isAbstract", False)
            properties["stereotype"] = node_data.get("stereotype", "")
            properties["attributes_count"] = len(uml_class.get("attributes", []))
            properties["methods_count"] = len(uml_class.get("methods", []))
        
        # BPMN Task
        elif "task" in node_data and node_data["task"]:
            task = node_data["task"]
            properties["name"] = task.get("name", "")
            properties["task_type"] = task.get("type", "task")
            properties["assignee"] = task.get("assignee", "")
        
        # BPMN Event
        elif "event" in node_data and node_data["event"]:
            event = node_data["event"]
            properties["name"] = event.get("name", "")
            properties["event_type"] = event.get("type", "start")
        
        # BPMN Gateway
        elif "gateway" in node_data and node_data["gateway"]:
            gateway = node_data["gateway"]
            properties["name"] = gateway.get("name", "")
            properties["gateway_type"] = gateway.get("type", "exclusive")
        
        return properties
    
    async def get_lineage(
        self,
        user_id: str,
        model_id: str,
        node_id: str,
        direction: str = "both"
    ) -> List[Dict[str, Any]]:
        """Get lineage for a node"""
        if not self.graph_client or not self.graph_client.is_connected():
            logger.warning("FalkorDB client not available for lineage query")
            return []
        
        graph_name = self._get_graph_name(user_id, model_id)
        
        # Build direction clause
        if direction == "upstream":
            rel_pattern = "<-[]-(ancestor)"
        elif direction == "downstream":
            rel_pattern = "-[]->(descendant)"
        else:  # both
            rel_pattern = "-[]-(related)"
        
        query = f"""
        MATCH (c:Concept {{id: $node_id}}){rel_pattern}
        RETURN DISTINCT related
        LIMIT 100
        """
        
        try:
            results = self.graph_client.execute_query(
                graph_name,
                query,
                {"node_id": node_id}
            )
            return results
        except Exception as e:
            logger.error("Failed to get lineage", error=str(e))
            return []
    
    async def get_impact(
        self,
        user_id: str,
        model_id: str,
        node_id: str
    ) -> List[Dict[str, Any]]:
        """Get impact analysis for a node"""
        if not self.graph_client or not self.graph_client.is_connected():
            logger.warning("FalkorDB client not available for impact analysis")
            return []
        
        graph_name = self._get_graph_name(user_id, model_id)
        
        query = """
        MATCH (c:Concept {id: $node_id})-[*1..3]->(impacted)
        RETURN DISTINCT impacted
        LIMIT 100
        """
        
        try:
            results = self.graph_client.execute_query(
                graph_name,
                query,
                {"node_id": node_id}
            )
            return results
        except Exception as e:
            logger.error("Failed to get impact analysis", error=str(e))
            return []