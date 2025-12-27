# backend/app/services/semantic_model_service.py
"""
Semantic Model Service
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
        self.graph_client = get_graph_client()
    
    def _get_graph_name(self, user_id: str, model_id: str) -> str:
        """Generate unique graph name for user and model"""
        return f"user_{user_id}_model_{model_id}"
    
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
        # Get diagram and model
        from app.repositories.diagram_repository import DiagramRepository
        diagram_repo = DiagramRepository(db)
        diagram = await diagram_repo.get(diagram_id)
        
        if not diagram:
            raise ValueError(f"Diagram {diagram_id} not found")
        
        graph_name = self._get_graph_name(user_id, diagram.model_id)
        
        stats = {
            "concepts_created": 0,
            "concepts_updated": 0,
            "relationships_created": 0,
            "errors": []
        }
        
        # Process nodes -> concepts
        for node in nodes:
            try:
                await self._sync_node_to_concept(graph_name, node, diagram.type)
                if node.get("_isNew"):
                    stats["concepts_created"] += 1
                else:
                    stats["concepts_updated"] += 1
            except Exception as e:
                logger.error("Failed to sync node", node_id=node.get("id"), error=str(e))
                stats["errors"].append({
                    "node_id": node.get("id"),
                    "error": str(e)
                })
        
        # Process edges -> relationships
        for edge in edges:
            try:
                await self._sync_edge_to_relationship(graph_name, edge, diagram.type)
                stats["relationships_created"] += 1
            except Exception as e:
                logger.error("Failed to sync edge", edge_id=edge.get("id"), error=str(e))
                stats["errors"].append({
                    "edge_id": edge.get("id"),
                    "error": str(e)
                })
        
        logger.info(
            "Diagram synced to graph",
            diagram_id=diagram_id,
            graph_name=graph_name,
            stats=stats
        )
        
        return stats
    
    async def _sync_node_to_concept(
        self,
        graph_name: str,
        node: Dict[str, Any],
        diagram_type: str
    ) -> None:
        """Sync a diagram node to a semantic concept"""
        node_id = node.get("id")
        node_type = node.get("type")
        node_data = node.get("data", {})
        
        # Determine concept type based on diagram type and node type
        concept_type = self._get_concept_type(diagram_type, node_type)
        
        # Extract properties based on node type
        properties = self._extract_node_properties(node_type, node_data)
        properties["diagram_type"] = diagram_type
        properties["position"] = node.get("position", {})
        
        # Check if concept exists
        existing = self.graph_client.execute_query(
            graph_name,
            "MATCH (c:Concept {id: $id}) RETURN c",
            {"id": node_id}
        )
        
        if existing:
            # Update existing concept
            self.graph_client.update_concept(graph_name, node_id, properties)
        else:
            # Create new concept
            self.graph_client.create_concept(
                graph_name,
                node_id,
                concept_type,
                properties
            )
    
    async def _sync_edge_to_relationship(
        self,
        graph_name: str,
        edge: Dict[str, Any],
        diagram_type: str
    ) -> None:
        """Sync a diagram edge to a semantic relationship"""
        source_id = edge.get("source")
        target_id = edge.get("target")
        edge_type = edge.get("type", "RELATES_TO")
        edge_data = edge.get("data", {})
        
        # Extract relationship properties
        properties = {
            "id": edge.get("id"),
            "label": edge_data.get("label", ""),
            "diagram_type": diagram_type
        }
        
        # Add type-specific properties
        if diagram_type == "ER":
            properties["cardinality"] = edge_data.get("cardinality", "1:N")
        elif diagram_type.startswith("UML"):
            properties["multiplicity"] = edge_data.get("multiplicity", "*")
        elif diagram_type == "BPMN":
            properties["condition"] = edge_data.get("condition", "")
        
        # Create relationship
        relationship_type = self._get_relationship_type(diagram_type, edge_type)
        self.graph_client.create_relationship(
            graph_name,
            source_id,
            target_id,
            relationship_type,
            properties
        )
    
    def _get_concept_type(self, diagram_type: str, node_type: str) -> str:
        """Determine semantic concept type from diagram node type"""
        if diagram_type == "ER":
            if "ENTITY" in node_type:
                return "Entity"
            elif "ATTRIBUTE" in node_type:
                return "Attribute"
        elif diagram_type.startswith("UML"):
            if "CLASS" in node_type or "INTERFACE" in node_type:
                return "Class"
            elif "PACKAGE" in node_type:
                return "Package"
            elif "COMPONENT" in node_type:
                return "Component"
            elif "STATE" in node_type:
                return "State"
            elif "ACTIVITY" in node_type:
                return "Activity"
        elif diagram_type == "BPMN":
            if "TASK" in node_type:
                return "Task"
            elif "EVENT" in node_type:
                return "Event"
            elif "GATEWAY" in node_type:
                return "Gateway"
            elif "POOL" in node_type or "LANE" in node_type:
                return "Swimlane"
        
        return "Concept"
    
    def _get_relationship_type(self, diagram_type: str, edge_type: str) -> str:
        """Determine semantic relationship type from diagram edge type"""
        # Map edge types to semantic relationships
        type_map = {
            "ER_RELATIONSHIP": "HAS_RELATIONSHIP",
            "ER_ATTRIBUTE_LINK": "HAS_ATTRIBUTE",
            "UML_ASSOCIATION": "ASSOCIATES_WITH",
            "UML_AGGREGATION": "AGGREGATES",
            "UML_COMPOSITION": "COMPOSES",
            "UML_GENERALIZATION": "EXTENDS",
            "UML_DEPENDENCY": "DEPENDS_ON",
            "UML_REALIZATION": "IMPLEMENTS",
            "UML_MESSAGE": "SENDS_MESSAGE",
            "UML_TRANSITION": "TRANSITIONS_TO",
            "BPMN_SEQUENCE_FLOW": "FLOWS_TO",
            "BPMN_MESSAGE_FLOW": "SENDS_MESSAGE",
            "BPMN_ASSOCIATION": "ASSOCIATES_WITH",
        }
        
        return type_map.get(edge_type, "RELATES_TO")
    
    def _extract_node_properties(
        self,
        node_type: str,
        node_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract properties from node data based on type"""
        properties = {
            "label": node_data.get("label", ""),
            "description": node_data.get("description", "")
        }
        
        # ER Entity
        if "entity" in node_data and node_data["entity"]:
            entity = node_data["entity"]
            properties["name"] = entity.get("name", "")
            properties["attributes"] = entity.get("attributes", [])
            properties["is_weak"] = entity.get("isWeak", False)
        
        # UML Class
        elif "class" in node_data and node_data["class"]:
            uml_class = node_data["class"]
            properties["name"] = uml_class.get("name", "")
            properties["is_abstract"] = uml_class.get("isAbstract", False)
            properties["stereotype"] = node_data.get("stereotype", "")
            properties["attributes"] = uml_class.get("attributes", [])
            properties["methods"] = uml_class.get("methods", [])
        
        # BPMN Task
        elif "task" in node_data and node_data["task"]:
            task = node_data["task"]
            properties["name"] = task.get("name", "")
            properties["task_type"] = task.get("type", "task")
            properties["assignee"] = task.get("assignee", "")
            properties["documentation"] = task.get("documentation", "")
        
        # BPMN Event
        elif "event" in node_data and node_data["event"]:
            event = node_data["event"]
            properties["name"] = event.get("name", "")
            properties["event_type"] = event.get("eventType", "")
            properties["event_definition"] = event.get("eventDefinition", "")
        
        # BPMN Gateway
        elif "gateway" in node_data and node_data["gateway"]:
            gateway = node_data["gateway"]
            properties["name"] = gateway.get("name", "")
            properties["gateway_type"] = gateway.get("gatewayType", "")
        
        # BPMN Pool/Lane
        elif "pool" in node_data and node_data["pool"]:
            pool = node_data["pool"]
            properties["name"] = pool.get("name", "")
            properties["lanes"] = pool.get("lanes", [])
        
        return properties
    
    async def get_lineage(
        self,
        user_id: str,
        model_id: str,
        concept_id: str,
        direction: str = "both",
        depth: int = 3
    ) -> List[Dict[str, Any]]:
        """Get lineage for a concept"""
        graph_name = self._get_graph_name(user_id, model_id)
        return self.graph_client.get_lineage(graph_name, concept_id, direction, depth)
    
    async def get_impact_analysis(
        self,
        user_id: str,
        model_id: str,
        concept_id: str
    ) -> Dict[str, Any]:
        """Get impact analysis for a concept"""
        graph_name = self._get_graph_name(user_id, model_id)
        return self.graph_client.get_impact_analysis(graph_name, concept_id)
    
    async def delete_model_graph(
        self,
        user_id: str,
        model_id: str
    ) -> bool:
        """Delete entire graph for a model"""
        graph_name = self._get_graph_name(user_id, model_id)
        return self.graph_client.delete_graph(graph_name)
    
    async def query_semantic_model(
        self,
        user_id: str,
        model_id: str,
        cypher_query: str,
        params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Execute custom Cypher query on semantic model"""
        graph_name = self._get_graph_name(user_id, model_id)
        return self.graph_client.execute_query(graph_name, cypher_query, params)