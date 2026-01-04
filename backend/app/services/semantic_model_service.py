# backend/app/services/semantic_model_service.py
"""
Semantic Model Service - Updated for Semantic Architect
Path: backend/app/services/semantic_model_service.py
"""

from typing import Any, Dict, List, Optional
import structlog
import json
import re

logger = structlog.get_logger()


class SemanticModelService:
    """Service for managing semantic model in FalkorDB graph database"""
    
    def __init__(self):
        self.graph_client = None
        try:
            from app.graph.client import get_graph_client
            self.graph_client = get_graph_client()
            if self.graph_client and self.graph_client.is_connected():
                logger.info("FalkorDB client initialized and connected")
            else:
                logger.warning("FalkorDB client initialized but not connected")
        except Exception as e:
            logger.warning(f"FalkorDB client initialization failed: {e}")
    
    def _sanitize_name_component(self, name: str) -> str:
        """
        Sanitize name component for graph name
        - Replace spaces with underscores
        - Remove special characters except forward slashes
        - Lowercase
        - Truncate to reasonable length
        """
        # Replace spaces and dashes with underscores
        sanitized = name.replace(" ", "_").replace("-", "_")
        # Remove special characters except forward slashes, keep only alphanumeric and underscores
        sanitized = re.sub(r'[^a-zA-Z0-9_/]', '', sanitized)
        # Lowercase
        sanitized = sanitized.lower()
        # Truncate to 50 characters per component
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
        
        NEW FORMAT per PRD: {workspace_name}/{diagram_name}/{username}
        
        Example: engineering_workspace/customer_order_diagram/john_doe
        
        Args:
            username: Username
            workspace_name: Workspace name
            diagram_name: Diagram name
            
        Returns:
            Sanitized graph name in format: workspace/diagram/user
        """
        safe_workspace = self._sanitize_name_component(workspace_name)
        safe_diagram = self._sanitize_name_component(diagram_name)
        safe_username = self._sanitize_name_component(username)
        
        # New format as per PRD: {workspace}/{diagram}/{user}
        graph_name = f"{safe_workspace}/{safe_diagram}/{safe_username}"
        
        logger.info(
            "Generated graph name",
            username=username,
            workspace=workspace_name,
            diagram=diagram_name,
            graph_name=graph_name
        )
        
        return graph_name
    
    async def sync_to_falkordb(
        self,
        graph_name: str,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Real-time synchronization to FalkorDB
        Called on every node/edge change
        
        Args:
            graph_name: FalkorDB graph reference
            nodes: List of diagram nodes
            edges: List of diagram edges
            
        Returns:
            Sync statistics
        """
        if not self.graph_client:
            logger.warning("FalkorDB client not available")
            return {"error": "FalkorDB client not initialized", "success": False}
        
        if not self.graph_client.is_connected():
            logger.warning("FalkorDB not connected")
            return {"error": "FalkorDB not connected", "success": False}
        
        try:
            # Clear existing graph
            clear_query = "MATCH (n) DETACH DELETE n"
            self.graph_client.query(graph_name, clear_query)
            
            logger.info(
                "Cleared existing graph",
                graph_name=graph_name
            )
            
            # Create nodes
            nodes_created = 0
            for node in nodes:
                try:
                    node_id = node.get('id', '')
                    node_type = node.get('type', 'Class')
                    node_data = node.get('data', {})
                    
                    # Prepare node properties
                    properties = {
                        'id': node_id,
                        'label': node_data.get('label', ''),
                        'type': node_type,
                        'stereotype': node_data.get('stereotype', ''),
                        'color': node_data.get('color', '#059669'),
                        'parentId': node_data.get('parentId', ''),
                    }
                    
                    # Add attributes as JSON string if present
                    if 'attributes' in node_data:
                        properties['attributes'] = json.dumps(node_data['attributes'])
                    
                    # Add methods as JSON string if present
                    if 'methods' in node_data:
                        properties['methods'] = json.dumps(node_data['methods'])
                    
                    # Add literals as JSON string if present
                    if 'literals' in node_data:
                        properties['literals'] = json.dumps(node_data['literals'])
                    
                    # Create Cypher query
                    node_label = node_type.upper()
                    query = f"""
                    CREATE (n:{node_label} {{
                        id: $id,
                        label: $label,
                        type: $type,
                        stereotype: $stereotype,
                        color: $color,
                        parentId: $parentId
                    }})
                    """
                    
                    # Add optional properties
                    if 'attributes' in properties:
                        query = query.replace(
                            "parentId: $parentId",
                            "parentId: $parentId, attributes: $attributes"
                        )
                    if 'methods' in properties:
                        query = query.replace(
                            "})",
                            ", methods: $methods})"
                        )
                    if 'literals' in properties:
                        query = query.replace(
                            "})",
                            ", literals: $literals})"
                        )
                    
                    self.graph_client.query(graph_name, query, properties)
                    nodes_created += 1
                    
                except Exception as node_error:
                    logger.error(
                        "Failed to create node",
                        node_id=node.get('id'),
                        error=str(node_error)
                    )
                    continue
            
            # Create relationships (edges)
            edges_created = 0
            for edge in edges:
                try:
                    source = edge.get('source', '')
                    target = edge.get('target', '')
                    edge_data = edge.get('data', {})
                    
                    rel_type = edge_data.get('type', 'RELATES_TO').upper().replace(' ', '_')
                    
                    properties = {
                        'source': source,
                        'target': target,
                        'sourceCardinality': edge_data.get('sourceCardinality', '1'),
                        'targetCardinality': edge_data.get('targetCardinality', '*'),
                        'label': edge_data.get('label', ''),
                        'color': edge_data.get('color', '#000000'),
                    }
                    
                    query = f"""
                    MATCH (a {{id: $source}}), (b {{id: $target}})
                    CREATE (a)-[r:{rel_type} {{
                        sourceCardinality: $sourceCardinality,
                        targetCardinality: $targetCardinality,
                        label: $label,
                        color: $color
                    }}]->(b)
                    """
                    
                    self.graph_client.query(graph_name, query, properties)
                    edges_created += 1
                    
                except Exception as edge_error:
                    logger.error(
                        "Failed to create edge",
                        edge_id=edge.get('id'),
                        error=str(edge_error)
                    )
                    continue
            
            logger.info(
                "FalkorDB sync completed",
                graph_name=graph_name,
                nodes_created=nodes_created,
                edges_created=edges_created
            )
            
            return {
                "success": True,
                "graph_name": graph_name,
                "nodes_created": nodes_created,
                "edges_created": edges_created,
            }
            
        except Exception as e:
            logger.error("FalkorDB sync failed", graph_name=graph_name, error=str(e))
            return {
                "success": False,
                "error": str(e),
                "graph_name": graph_name,
            }
    
    def get_graph_stats(self, graph_name: str) -> Dict[str, Any]:
        """
        Get statistics about a graph
        
        Args:
            graph_name: FalkorDB graph reference
            
        Returns:
            Graph statistics
        """
        if not self.graph_client or not self.graph_client.is_connected():
            return {"error": "FalkorDB not available"}
        
        try:
            # Count nodes
            node_query = "MATCH (n) RETURN count(n) as count"
            node_result = self.graph_client.query(graph_name, node_query)
            total_nodes = node_result.result_set[0][0] if node_result.result_set else 0
            
            # Count edges
            edge_query = "MATCH ()-[r]->() RETURN count(r) as count"
            edge_result = self.graph_client.query(graph_name, edge_query)
            total_edges = edge_result.result_set[0][0] if edge_result.result_set else 0
            
            return {
                "total_nodes": total_nodes,
                "total_edges": total_edges,
                "graph_name": graph_name,
            }
            
        except Exception as e:
            logger.error("Failed to get graph stats", graph_name=graph_name, error=str(e))
            return {"error": str(e)}