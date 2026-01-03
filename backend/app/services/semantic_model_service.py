# backend/app/services/semantic_model_service.py
"""
Semantic Model Service - COMPLETE FIX
Path: backend/app/services/semantic_model_service.py

CRITICAL FIXES:
1. Never update graph_name if already set - prevents unique constraint violations
2. Proper session rollback on errors
3. Generate graph_name should be used only once during creation
"""
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
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
        diagram_name: str,
        add_random_suffix: bool = True
    ) -> str:
        """
        Generate unique graph name for a diagram
        
        CRITICAL: One graph per diagram
        Format: user_{username}_workspace_{workspace}_diagram_{diagram_name}_{random}
        
        Example: user_john_workspace_engineering_diagram_customer_order_er_a1b2c3d4
        
        Args:
            username: Username
            workspace_name: Workspace name
            diagram_name: Diagram name
            add_random_suffix: Whether to add random suffix (default True for uniqueness)
            
        Returns:
            Sanitized graph name
        """
        import uuid
        
        safe_username = self._sanitize_name_component(username)
        safe_workspace = self._sanitize_name_component(workspace_name)
        safe_diagram = self._sanitize_name_component(diagram_name)
        
        if add_random_suffix:
            graph_name = f"user_{safe_username}_workspace_{safe_workspace}_diagram_{safe_diagram}_{uuid.uuid4().hex[:8]}"
        else:
            graph_name = f"user_{safe_username}_workspace_{safe_workspace}_diagram_{safe_diagram}"
        
        logger.info(
            "Generated graph name",
            username=username,
            workspace=workspace_name,
            diagram=diagram_name,
            graph_name=graph_name,
            with_random_suffix=add_random_suffix
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
        - NEVER updates graph_name if already set (prevents unique constraint violations)
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
            
            # CRITICAL FIX: Use existing graph_name if already set
            # Never recalculate to avoid unique constraint violations
            if diagram.graph_name:
                graph_name = diagram.graph_name
                logger.info(
                    "Using existing graph_name from diagram",
                    diagram_id=diagram_id,
                    graph_name=graph_name
                )
            else:
                # Only generate if not set (shouldn't happen after creation)
                result = await db.execute(
                    select(Workspace).where(Workspace.id == workspace_id)
                )
                workspace = result.scalar_one_or_none()
                
                result = await db.execute(
                    select(User).where(User.id == user_id)
                )
                user = result.scalar_one_or_none()
                
                if not workspace or not user:
                    error_msg = "Workspace or user not found"
                    logger.error(error_msg)
                    stats["errors"].append(error_msg)
                    return stats
                
                # Generate graph name with random suffix for uniqueness
                graph_name = self.generate_graph_name(
                    user.username,
                    workspace.name,
                    diagram.name,
                    add_random_suffix=True
                )
                
                # CRITICAL FIX: Update diagram with graph_name ONLY if not already set
                # Use proper error handling to prevent session corruption
                try:
                    diagram.graph_name = graph_name
                    await db.commit()
                    await db.refresh(diagram)
                    logger.info(
                        "Set diagram graph_name for first time",
                        diagram_id=diagram_id,
                        graph_name=graph_name
                    )
                except IntegrityError as ie:
                    # CRITICAL: Rollback session on integrity error
                    await db.rollback()
                    error_msg = f"Failed to set graph_name: {str(ie)}"
                    logger.error(
                        "Integrity error setting graph_name",
                        error=error_msg,
                        diagram_id=diagram_id
                    )
                    stats["errors"].append(error_msg)
                    return stats
                except Exception as e:
                    await db.rollback()
                    error_msg = f"Failed to update diagram: {str(e)}"
                    logger.error(error_msg)
                    stats["errors"].append(error_msg)
                    return stats
            
            stats["graph_name"] = graph_name
            stats["falkordb_available"] = True
            stats["falkordb_connected"] = self.graph_client.is_connected()
            
            # Initialize graph if it doesn't exist
            try:
                self.graph_client.init_graph(graph_name)
                logger.info(f"Initialized graph: {graph_name}")
            except Exception as e:
                logger.warning(f"Graph initialization warning: {e}")
            
            # Get diagram type for node/edge extraction
            diagram_type = diagram.notation if hasattr(diagram, 'notation') else "ER"
            
            # Sync nodes
            for node in nodes:
                try:
                    created = await self._sync_node_to_graph(
                        graph_name=graph_name,
                        node=node,
                        diagram_type=diagram_type,
                        user_id=user_id,
                        workspace_id=workspace_id,
                        diagram_id=diagram_id,
                        diagram_name=diagram.name
                    )
                    
                    if created:
                        stats["nodes_created"] += 1
                    else:
                        stats["nodes_updated"] += 1
                        
                except Exception as e:
                    error_msg = f"Failed to sync node {node.get('id', 'unknown')}: {str(e)}"
                    logger.error(error_msg)
                    stats["errors"].append(error_msg)
            
            # Sync edges
            for edge in edges:
                try:
                    success = await self._sync_edge_to_graph(
                        graph_name=graph_name,
                        edge=edge,
                        diagram_type=diagram_type,
                        user_id=user_id,
                        workspace_id=workspace_id,
                        diagram_id=diagram_id
                    )
                    
                    if success:
                        stats["edges_created"] += 1
                        
                except Exception as e:
                    error_msg = f"Failed to sync edge {edge.get('id', 'unknown')}: {str(e)}"
                    logger.error(error_msg)
                    stats["errors"].append(error_msg)
            
            logger.info(
                "Diagram sync completed",
                diagram_id=diagram_id,
                graph_name=graph_name,
                nodes_created=stats["nodes_created"],
                nodes_updated=stats["nodes_updated"],
                edges_created=stats["edges_created"],
                errors_count=len(stats["errors"])
            )
            
            return stats
            
        except Exception as e:
            # CRITICAL: Ensure session is rolled back on any error
            try:
                await db.rollback()
            except:
                pass
            
            error_msg = f"Sync error: {str(e)}"
            logger.error("Fatal error in diagram sync", error=error_msg)
            stats["errors"].append(error_msg)
            return stats
    
    def _extract_node_properties(
        self,
        node: Dict[str, Any],
        diagram_type: str
    ) -> tuple[str, str, Dict[str, Any]]:
        """
        Extract node label (type), name, and properties from node data
        
        Returns:
            Tuple of (node_label, node_name, properties_dict)
        """
        node_type = node.get("type", "Entity")
        data = node.get("data", {})
        
        # Default values
        node_name = data.get("name", data.get("label", "Unnamed"))
        node_label = "Entity"
        properties = {}
        
        # Extract based on diagram type
        if diagram_type == "ER":
            if node_type == "entity":
                node_label = "Entity"
                properties = {
                    "entity_type": data.get("entityType", "regular"),
                    "attributes": json.dumps(data.get("attributes", [])),
                    "is_weak": data.get("isWeak", False)
                }
            elif node_type == "attribute":
                node_label = "Attribute"
                properties = {
                    "data_type": data.get("dataType", "string"),
                    "is_primary": data.get("isPrimary", False),
                    "is_unique": data.get("isUnique", False),
                    "is_nullable": data.get("isNullable", True)
                }
                
        elif diagram_type.startswith("UML_CLASS"):
            if node_type in ["class", "interface", "abstract"]:
                node_label = "Class"
                properties = {
                    "class_type": node_type,
                    "attributes": json.dumps(data.get("attributes", [])),
                    "methods": json.dumps(data.get("methods", [])),
                    "is_abstract": data.get("isAbstract", False)
                }
                
        elif diagram_type == "BPMN":
            node_label = data.get("bpmnType", "Task").title()
            properties = {
                "bpmn_type": data.get("bpmnType", "task"),
                "description": data.get("description", "")
            }
        
        return node_label, node_name, properties
    
    async def _sync_node_to_graph(
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
        Sync single node to graph
        
        Returns:
            True if created (new), False if updated (existing)
        """
        node_id = node.get("id")
        if not node_id:
            logger.warning("Node missing ID, skipping")
            return False
        
        # Extract node properties
        node_label, node_name, extracted_properties = self._extract_node_properties(node, diagram_type)
        
        # Get position
        position = node.get("position", {})
        
        # Build complete properties
        properties = {
            "id": node_id,
            "name": node_name,
            "diagram_type": diagram_type,
            "node_type": node.get("type", "entity"),
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
        edge_type = edge.get("type", "relationship")
        data = edge.get("data", {})
        
        # Default values
        relationship_name = data.get("name", data.get("label", "relates_to"))
        relationship_type = "RELATES_TO"
        properties = {}
        
        # Extract based on diagram type
        if diagram_type == "ER":
            relationship_name = data.get("name", "relationship")
            relationship_type = "RELATES_TO"
            properties = {
                "cardinality": data.get("cardinality", "1:N"),
                "source_cardinality": data.get("sourceCardinality", "1"),
                "target_cardinality": data.get("targetCardinality", "N"),
                "is_identifying": data.get("isIdentifying", False)
            }
            
        elif diagram_type.startswith("UML_CLASS"):
            relationship_name = data.get("name", "association")
            
            # Map UML relationship types
            if edge_type == "association":
                relationship_type = "ASSOCIATED_WITH"
            elif edge_type == "aggregation":
                relationship_type = "AGGREGATES"
            elif edge_type == "composition":
                relationship_type = "COMPOSED_OF"
            elif edge_type == "generalization":
                relationship_type = "EXTENDS"
            elif edge_type == "dependency":
                relationship_type = "DEPENDS_ON"
            elif edge_type == "realization":
                relationship_type = "IMPLEMENTS"
            else:
                relationship_type = "ASSOCIATED_WITH"
            
            properties = {
                "multiplicity": data.get("multiplicity", ""),
                "source_multiplicity": data.get("sourceMultiplicity", ""),
                "target_multiplicity": data.get("targetMultiplicity", "")
            }
            
        elif diagram_type == "BPMN":
            relationship_name = data.get("name", "flow")
            if edge_type == "sequence":
                relationship_type = "FLOWS_TO"
            elif edge_type == "message":
                relationship_type = "SENDS_MESSAGE_TO"
            else:
                relationship_type = "RELATES_TO"
        
        return relationship_name, relationship_type, properties
    
    async def _sync_edge_to_graph(
        self,
        graph_name: str,
        edge: Dict[str, Any],
        diagram_type: str,
        user_id: str,
        workspace_id: str,
        diagram_id: str
    ) -> bool:
        """
        Sync single edge to graph
        
        Returns:
            True if successful
        """
        edge_id = edge.get("id")
        source = edge.get("source")
        target = edge.get("target")
        
        if not edge_id or not source or not target:
            logger.warning("Edge missing required fields, skipping", edge_id=edge_id)
            return False
        
        # Extract edge properties
        relationship_name, relationship_type, extracted_properties = self._extract_edge_properties(edge, diagram_type)
        
        # Build complete properties
        properties = {
            "id": edge_id,
            "name": relationship_name,
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