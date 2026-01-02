# backend/app/services/semantic_model_service.py
"""
Semantic Model Service - CORRECT ARCHITECTURE
Path: backend/app/services/semantic_model_service.py

CRITICAL ARCHITECTURE FIX:
- One graph per diagram (not per user+model)
- Graph name format: user_{username}_workspace_{workspace}_diagram_{diagram_name}
- Each node/edge has user_id property
- Graph name stored in PostgreSQL diagram table
- Complete isolation between diagrams
"""
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog
import json
import re

logger = structlog.get_logger()


class SemanticModelService:
    """Service for managing semantic model in graph database"""
    
    def __init__(self):
        self.graph_client = None
        try:
            from app.graph.client import get_graph_client
            self.graph_client = get_graph_client()
            logger.info("FalkorDB client initialized")
        except Exception as e:
            logger.warning(f"FalkorDB client initialization failed: {e}")
    
    def _sanitize_name_component(self, name: str) -> str:
        """
        Sanitize name component for graph name
        - Replace spaces with underscores
        - Remove special characters
        - Lowercase
        - Truncate to reasonable length
        """
        # Replace spaces and dashes with underscores
        sanitized = name.replace(" ", "_").replace("-", "_")
        # Remove special characters, keep only alphanumeric and underscores
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '', sanitized)
        # Lowercase
        sanitized = sanitized.lower()
        # Truncate to 50 characters
        sanitized = sanitized[:50]
        return sanitized
    
    def generate_graph_name(
        self,
        username: str,
        workspace_name: str,
        diagram_name: str
    ) -> str:
        """
        Generate unique graph name for a diagram
        
        CRITICAL: One graph per diagram
        Format: user_{username}_workspace_{workspace}_diagram_{diagram_name}
        
        Example: user_john_workspace_engineering_diagram_customer_order_er
        
        Args:
            username: Username
            workspace_name: Workspace name
            diagram_name: Diagram name
            
        Returns:
            Sanitized graph name
        """
        safe_username = self._sanitize_name_component(username)
        safe_workspace = self._sanitize_name_component(workspace_name)
        safe_diagram = self._sanitize_name_component(diagram_name)
        
        graph_name = f"user_{safe_username}_workspace_{safe_workspace}_diagram_{safe_diagram}"
        
        logger.info(
            "Generated graph name",
            username=username,
            workspace=workspace_name,
            diagram=diagram_name,
            graph_name=graph_name
        )
        
        return graph_name
    
    async def sync_diagram_to_graph(
        self,
        db: AsyncSession,
        diagram_id: str,
        user_id: str,
        workspace_id: str,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Sync diagram nodes and edges to FalkorDB graph database
        
        CRITICAL ARCHITECTURE:
        - Creates one graph per diagram
        - Stores graph name in PostgreSQL diagram table
        - Adds user_id to all nodes and edges
        - Uses actual entity/class names for nodes
        - Uses relationship names and cardinality for edges
        
        Args:
            db: Database session
            diagram_id: Diagram UUID
            user_id: User UUID
            workspace_id: Workspace UUID
            nodes: List of diagram nodes
            edges: List of diagram edges
            
        Returns:
            Sync statistics
        """
        stats = {
            "diagram_id": diagram_id,
            "graph_name": None,
            "falkordb_available": False,
            "falkordb_connected": False,
            "nodes_created": 0,
            "nodes_updated": 0,
            "edges_created": 0,
            "errors": []
        }
        
        if not self.graph_client:
            logger.warning("FalkorDB client not available")
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
            from app.models.workspace import Workspace
            from app.models.user import User
            
            # Get diagram
            result = await db.execute(
                select(Diagram).where(Diagram.id == diagram_id)
            )
            diagram = result.scalar_one_or_none()
            
            if not diagram:
                error_msg = f"Diagram {diagram_id} not found"
                logger.error(error_msg)
                stats["errors"].append(error_msg)
                return stats
            
            # Get workspace
            result = await db.execute(
                select(Workspace).where(Workspace.id == workspace_id)
            )
            workspace = result.scalar_one_or_none()
            
            if not workspace:
                error_msg = f"Workspace {workspace_id} not found"
                logger.error(error_msg)
                stats["errors"].append(error_msg)
                return stats
            
            # Get user
            result = await db.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                error_msg = f"User {user_id} not found"
                logger.error(error_msg)
                stats["errors"].append(error_msg)
                return stats
            
            # CRITICAL: Generate graph name based on diagram
            graph_name = self.generate_graph_name(
                user.username,
                workspace.name,
                diagram.name
            )
            
            # CRITICAL: Update diagram with graph_name if not set
            if diagram.graph_name != graph_name:
                diagram.graph_name = graph_name
                await db.commit()
                logger.info(
                    "Updated diagram with graph name",
                    diagram_id=diagram_id,
                    graph_name=graph_name
                )
            
            stats["graph_name"] = graph_name
            stats["falkordb_available"] = True
            stats["falkordb_connected"] = True
            
            # Process nodes with user_id
            for node in nodes:
                try:
                    node_id = node.get("id")
                    if not node_id:
                        continue
                    
                    created = self._sync_node_to_concept(
                        graph_name,
                        node,
                        diagram.notation,
                        user_id=str(user_id),
                        workspace_id=str(workspace_id),
                        diagram_id=str(diagram_id),
                        diagram_name=diagram.name
                    )
                    
                    if created:
                        stats["nodes_created"] += 1
                    else:
                        stats["nodes_updated"] += 1
                        
                except Exception as e:
                    error_msg = f"Failed to sync node {node.get('id')}: {str(e)}"
                    logger.error(error_msg)
                    stats["errors"].append(error_msg)
            
            # Process edges with user_id
            for edge in edges:
                try:
                    edge_id = edge.get("id")
                    if not edge_id:
                        continue
                    
                    success = self._sync_edge_to_relationship(
                        graph_name,
                        edge,
                        diagram.notation,
                        user_id=str(user_id),
                        workspace_id=str(workspace_id),
                        diagram_id=str(diagram_id)
                    )
                    
                    if success:
                        stats["edges_created"] += 1
                    
                except Exception as e:
                    error_msg = f"Failed to sync edge {edge.get('id')}: {str(e)}"
                    logger.error(error_msg)
                    stats["errors"].append(error_msg)
            
            logger.info(
                "✅ Diagram synced to FalkorDB",
                diagram_id=diagram_id,
                graph_name=graph_name,
                nodes_created=stats["nodes_created"],
                nodes_updated=stats["nodes_updated"],
                edges_created=stats["edges_created"]
            )
            
        except Exception as e:
            error_msg = f"Failed to sync diagram: {str(e)}"
            logger.error(error_msg)
            stats["errors"].append(error_msg)
        
        return stats
    
    def _extract_node_name_and_properties(
        self,
        node: Dict[str, Any],
        diagram_type: str
    ) -> tuple[str, Dict[str, Any], str]:
        """
        Extract actual node name, properties, and label from nested data structure
        
        Returns:
            Tuple of (node_name, properties_dict, node_label)
        """
        node_data = node.get("data", {})
        node_type = node.get("type", "")
        
        # Default values
        node_name = "Unnamed"
        properties = {}
        node_label = "Concept"
        
        # ER DIAGRAMS - Extract entity data
        if diagram_type == "ER" or node_type.startswith("ER_"):
            node_name = node_data.get("label", "Unnamed Entity")
            node_label = "Entity"
            
            # Extract attributes array
            attributes = node_data.get("attributes", [])
            properties["attributes"] = json.dumps(attributes) if attributes else "[]"
            properties["attribute_count"] = len(attributes)
            
            # Extract primary keys
            primary_keys = [
                attr.get("name") 
                for attr in attributes 
                if attr.get("isPrimaryKey", False)
            ]
            properties["primary_keys"] = json.dumps(primary_keys)
            
            # Extract foreign keys
            foreign_keys = [
                attr.get("name") 
                for attr in attributes 
                if attr.get("isForeignKey", False)
            ]
            properties["foreign_keys"] = json.dumps(foreign_keys)
            
            # Entity-specific properties
            properties["is_weak"] = node_data.get("isWeak", False)
            properties["color"] = node_data.get("color", "#ffffff")
            properties["text_color"] = node_data.get("textColor", "#000000")
        
        # UML CLASS DIAGRAMS - Extract class data
        elif diagram_type.startswith("UML_CLASS") or node_type.startswith("UML_CLASS"):
            node_name = node_data.get("label", "Unnamed Class")
            node_label = "Class"
            
            # Extract attributes
            attributes = node_data.get("attributes", [])
            properties["attributes"] = json.dumps(attributes) if attributes else "[]"
            properties["attribute_count"] = len(attributes)
            
            # Extract methods
            methods = node_data.get("methods", [])
            properties["methods"] = json.dumps(methods) if methods else "[]"
            properties["method_count"] = len(methods)
            
            # Class-specific properties
            properties["is_abstract"] = node_data.get("isAbstract", False)
            properties["stereotype"] = node_data.get("stereotype", "")
            properties["class_type"] = node_data.get("classType", "class")
            properties["visibility"] = node_data.get("visibility", "public")
            properties["color"] = node_data.get("color", "#ffffff")
            properties["text_color"] = node_data.get("textColor", "#000000")
        
        # UML SEQUENCE DIAGRAMS - Extract lifeline data
        elif diagram_type.startswith("UML_SEQUENCE") or node_type.startswith("UML_LIFELINE"):
            node_name = node_data.get("label", "Unnamed Object")
            node_label = "Lifeline"
            
            properties["stereotype"] = node_data.get("stereotype", "")
            properties["lifeline_height"] = node_data.get("lifelineHeight", 400)
            properties["color"] = node_data.get("color", "#ffffff")
        
        # BPMN DIAGRAMS - Extract task/event/gateway data
        elif diagram_type == "BPMN":
            if node_type.startswith("BPMN_TASK") or "task" in node_type.lower():
                node_name = node_data.get("label", "Unnamed Task")
                node_label = "Task"
                properties["task_type"] = node_data.get("taskType", "task")
                
            elif node_type.startswith("BPMN_") and "EVENT" in node_type:
                node_name = node_data.get("label", "Unnamed Event")
                node_label = "Event"
                properties["event_type"] = node_data.get("eventType", "start")
                properties["event_trigger"] = node_data.get("eventTrigger", "none")
                
            elif node_type.startswith("BPMN_GATEWAY"):
                node_name = node_data.get("label", "Unnamed Gateway")
                node_label = "Gateway"
                properties["gateway_type"] = node_data.get("gatewayType", "exclusive")
                
            elif node_type.startswith("BPMN_POOL") or node_type.startswith("BPMN_LANE"):
                node_name = node_data.get("label", "Unnamed Pool")
                node_label = "Pool"
                properties["pool_type"] = node_data.get("poolType", "pool")
                properties["width"] = node_data.get("width", 400)
                properties["height"] = node_data.get("height", 200)
            
            properties["color"] = node_data.get("color", "#ffffff")
        
        # GENERIC/FALLBACK
        else:
            node_name = node_data.get("label", node_data.get("name", "Unnamed"))
            node_label = "Concept"
        
        return node_name, properties, node_label
    
    def _sync_node_to_concept(
        self,
        graph_name: str,
        node: Dict[str, Any],
        diagram_type: str,
        user_id: str,
        workspace_id: str,
        diagram_id: str,
        diagram_name: str
    ) -> bool:
        """
        Sync node to concept
        
        CRITICAL: Adds user_id, workspace_id, diagram_id to all nodes
        
        Returns True if created, False if updated
        """
        if not self.graph_client or not self.graph_client.is_connected():
            return False
        
        node_id = node.get("id")
        node_type = node.get("type")
        position = node.get("position", {})
        
        # Extract actual name and properties
        node_name, extracted_properties, node_label = self._extract_node_name_and_properties(
            node,
            diagram_type
        )
        
        # Build complete properties dict
        properties = {
            "id": node_id,
            "name": node_name,  # Actual entity/class name!
            "diagram_type": diagram_type,
            "node_type": node_type,
            "position_x": position.get("x", 0),
            "position_y": position.get("y", 0),
            # CRITICAL: Add user/workspace/diagram context
            "user_id": user_id,
            "workspace_id": workspace_id,
            "diagram_id": diagram_id,
            "diagram_name": diagram_name
        }
        
        # Merge extracted properties
        properties.update(extracted_properties)
        
        try:
            # Check if exists
            existing = self.graph_client.execute_query(
                graph_name,
                "MATCH (c {id: $id}) RETURN c",
                {"id": node_id}
            )
            
            if existing and len(existing) > 0:
                # Update
                self.graph_client.update_concept(graph_name, node_id, properties)
                logger.info(
                    f"Updated {node_label}",
                    graph_name=graph_name,
                    node_name=node_name
                )
                return False
            else:
                # Create
                self.graph_client.create_concept(
                    graph_name,
                    node_id,
                    node_label,
                    properties
                )
                logger.info(
                    f"Created {node_label}",
                    graph_name=graph_name,
                    node_name=node_name
                )
                return True
                
        except Exception as e:
            logger.error(
                "Failed to sync node",
                node_id=node_id,
                error=str(e)
            )
            raise
    
    def _extract_edge_properties(
        self,
        edge: Dict[str, Any],
        diagram_type: str
    ) -> tuple[str, str, Dict[str, Any]]:
        """
        Extract relationship name, type, and properties from edge data
        
        Returns:
            Tuple of (relationship_name, relationship_type, properties_dict)
        """
        edge_data = edge.get("data", {})
        edge_type = edge.get("type", "")
        
        relationship_name = ""
        relationship_type = "RELATED_TO"
        properties = {}
        
        # ER DIAGRAMS
        if diagram_type == "ER" or edge_type.startswith("ER_"):
            relationship_name = edge_data.get("label", "")
            relationship_type = "RELATES_TO"
            
            # CRITICAL: Extract cardinality
            properties["source_cardinality"] = edge_data.get("sourceCardinality", "1")
            properties["target_cardinality"] = edge_data.get("targetCardinality", "N")
            properties["is_identifying"] = edge_data.get("isIdentifying", False)
            properties["color"] = edge_data.get("color", "#6b7280")
        
        # UML CLASS DIAGRAMS
        elif diagram_type.startswith("UML_CLASS") or edge_type.startswith("UML_"):
            relationship_name = edge_data.get("label", "")
            
            association_type = edge_data.get("associationType", "association")
            type_mapping = {
                "association": "ASSOCIATES_WITH",
                "generalization": "EXTENDS",
                "dependency": "DEPENDS_ON",
                "aggregation": "AGGREGATES",
                "composition": "COMPOSES",
                "realization": "IMPLEMENTS"
            }
            relationship_type = type_mapping.get(association_type, "ASSOCIATES_WITH")
            
            properties["source_multiplicity"] = edge_data.get("sourceMultiplicity", "1")
            properties["target_multiplicity"] = edge_data.get("targetMultiplicity", "1")
            properties["association_type"] = association_type
            properties["color"] = edge_data.get("color", "#6b7280")
        
        # UML SEQUENCE DIAGRAMS
        elif diagram_type.startswith("UML_SEQUENCE") or "MESSAGE" in edge_type:
            relationship_name = edge_data.get("label", "message()")
            relationship_type = "SENDS_MESSAGE"
            
            properties["message_type"] = edge_data.get("messageType", "sync")
            properties["sequence"] = edge_data.get("sequence", 1)
            properties["color"] = edge_data.get("color", "#6b7280")
        
        # BPMN DIAGRAMS
        elif diagram_type == "BPMN":
            relationship_name = edge_data.get("label", "")
            
            if "SEQUENCE" in edge_type:
                relationship_type = "SEQUENCE_FLOW"
                properties["condition"] = edge_data.get("condition", "")
                properties["is_default"] = edge_data.get("isDefault", False)
            elif "MESSAGE" in edge_type:
                relationship_type = "MESSAGE_FLOW"
            else:
                relationship_type = "ASSOCIATION"
            
            properties["color"] = edge_data.get("color", "#6b7280")
        
        # GENERIC
        else:
            relationship_name = edge_data.get("label", "")
            relationship_type = "RELATED_TO"
        
        return relationship_name, relationship_type, properties
    
    def _sync_edge_to_relationship(
        self,
        graph_name: str,
        edge: Dict[str, Any],
        diagram_type: str,
        user_id: str,
        workspace_id: str,
        diagram_id: str
    ) -> bool:
        """
        Sync edge to relationship
        
        CRITICAL: Adds user_id, workspace_id, diagram_id to all edges
        """
        if not self.graph_client or not self.graph_client.is_connected():
            return False
        
        edge_id = edge.get("id")
        source = edge.get("source")
        target = edge.get("target")
        
        # Extract relationship details
        relationship_name, relationship_type, extracted_properties = self._extract_edge_properties(
            edge,
            diagram_type
        )
        
        # Build properties
        properties = {
            "id": edge_id,
            "name": relationship_name,
            "label": relationship_name,
            "diagram_type": diagram_type,
            "edge_type": edge.get("type", ""),
            # CRITICAL: Add user/workspace/diagram context
            "user_id": user_id,
            "workspace_id": workspace_id,
            "diagram_id": diagram_id
        }
        
        # Merge extracted properties
        properties.update(extracted_properties)
        
        try:
            success = self.graph_client.create_relationship(
                graph_name,
                source,
                target,
                relationship_type,
                properties
            )
            
            if success:
                logger.info(
                    f"Created relationship",
                    graph_name=graph_name,
                    name=relationship_name,
                    type=relationship_type,
                    cardinality=f"{properties.get('source_cardinality', '')}:{properties.get('target_cardinality', '')}"
                )
            
            return success
            
        except Exception as e:
            logger.error(
                "Failed to sync edge",
                edge_id=edge_id,
                error=str(e)
            )
            return False
    
    async def delete_diagram_graph(
        self,
        graph_name: str
    ) -> bool:
        """
        Delete entire graph for a diagram
        
        Args:
            graph_name: Name of the graph to delete
            
        Returns:
            True if successful
        """
        if not self.graph_client or not self.graph_client.is_connected():
            return False
        
        try:
            success = self.graph_client.delete_graph(graph_name)
            if success:
                logger.info(
                    "Deleted diagram graph",
                    graph_name=graph_name
                )
            return success
        except Exception as e:
            logger.error(
                "Failed to delete graph",
                graph_name=graph_name,
                error=str(e)
            )
            return False