# backend/app/services/semantic_model_service.py
"""
Semantic Model Service - FIXED for proper FalkorDB sync
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
        """Sanitize name component for graph name"""
        sanitized = name.replace(" ", "_").replace("-", "_")
        sanitized = re.sub(r'[^a-zA-Z0-9_/]', '', sanitized)
        sanitized = sanitized.lower()
        sanitized = sanitized[:50]
        return sanitized
    
    def generate_graph_name(
        self,
        username: str,
        workspace_name: str,
        diagram_name: str
    ) -> str:
        """Generate unique graph name for a diagram"""
        safe_workspace = self._sanitize_name_component(workspace_name)
        safe_diagram = self._sanitize_name_component(diagram_name)
        safe_username = self._sanitize_name_component(username or "user")
        
        graph_name = f"{safe_workspace}/{safe_diagram}/{safe_username}"
        
        logger.info(
            "Generated graph name",
            username=username,
            workspace=workspace_name,
            diagram=diagram_name,
            graph_name=graph_name
        )
        
        return graph_name
    
    def _escape_string(self, value: str) -> str:
        """Escape string for Cypher query"""
        if value is None:
            return ""
        # Escape single quotes and backslashes
        escaped = str(value).replace("\\", "\\\\").replace("'", "\\'")
        return escaped
    
    def _serialize_property(self, value: Any) -> str:
        """Serialize property value for Cypher query"""
        if value is None:
            return "null"
        elif isinstance(value, bool):
            return "true" if value else "false"
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, (list, dict)):
            # Serialize as JSON string
            json_str = json.dumps(value)
            return f"'{self._escape_string(json_str)}'"
        else:
            return f"'{self._escape_string(str(value))}'"
    
    async def sync_to_falkordb(
        self,
        graph_name: str,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        FIXED: Real-time synchronization to FalkorDB with proper data extraction
        
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
            logger.info(
                "Starting FalkorDB sync",
                graph_name=graph_name,
                node_count=len(nodes),
                edge_count=len(edges)
            )
            
            # Clear existing graph
            clear_query = "MATCH (n) DETACH DELETE n"
            self.graph_client.query(graph_name, clear_query)
            logger.info("Cleared existing graph", graph_name=graph_name)
            
            # Create nodes
            nodes_created = 0
            node_id_mapping = {}  # Track which nodes exist
            
            for node in nodes:
                try:
                    node_id = node.get('id', '')
                    node_type = node.get('type', 'Class')
                    node_data = node.get('data', {})
                    position = node.get('position', {})
                    
                    # Extract node name/label
                    node_label = node_data.get('label', node_data.get('name', 'Unnamed'))
                    
                    # Build properties
                    properties = {
                        'id': node_id,
                        'label': node_label,
                        'node_type': node_type,
                        'x': position.get('x', 0),
                        'y': position.get('y', 0),
                    }
                    
                    # Add optional properties
                    if 'color' in node_data:
                        properties['color'] = node_data['color']
                    if 'stereotype' in node_data:
                        properties['stereotype'] = node_data['stereotype']
                    
                    # Handle parentId for package containment
                    if 'parentId' in node_data and node_data['parentId']:
                        properties['parent_id'] = node_data['parentId']
                    
                    # Handle attributes (for classes, objects, interfaces)
                    if 'attributes' in node_data and node_data['attributes']:
                        # Store as JSON string
                        properties['attributes'] = json.dumps(node_data['attributes'])
                    
                    # Handle methods (for classes, interfaces)
                    if 'methods' in node_data and node_data['methods']:
                        properties['methods'] = json.dumps(node_data['methods'])
                    
                    # Handle literals (for enumerations)
                    if 'literals' in node_data and node_data['literals']:
                        properties['literals'] = json.dumps(node_data['literals'])
                    
                    # Build property string for Cypher
                    prop_strings = []
                    for key, value in properties.items():
                        prop_strings.append(f"{key}: {self._serialize_property(value)}")
                    
                    props_clause = "{" + ", ".join(prop_strings) + "}"
                    
                    # Use node type as label, add Concept as secondary label
                    # This allows filtering by type OR all concepts
                    label = f"{node_type.upper()}:Concept"
                    
                    # Create node query
                    create_query = f"CREATE (n:{label} {props_clause}) RETURN n"
                    
                    self.graph_client.query(graph_name, create_query)
                    nodes_created += 1
                    node_id_mapping[node_id] = True
                    
                    logger.debug(
                        "Created node in FalkorDB",
                        node_id=node_id,
                        node_type=node_type,
                        label=node_label
                    )
                    
                except Exception as node_error:
                    logger.error(
                        "Failed to create node",
                        node_id=node.get('id'),
                        error=str(node_error),
                        node_data=node
                    )
                    continue
            
            # Create edges (relationships)
            edges_created = 0
            for edge in edges:
                try:
                    edge_id = edge.get('id', '')
                    source_id = edge.get('source', '')
                    target_id = edge.get('target', '')
                    edge_data = edge.get('data', {})
                    
                    # Only create edge if both nodes exist
                    if source_id not in node_id_mapping or target_id not in node_id_mapping:
                        logger.warning(
                            "Skipping edge with missing nodes",
                            edge_id=edge_id,
                            source=source_id,
                            target=target_id
                        )
                        continue
                    
                    # Extract edge properties
                    edge_type = edge_data.get('type', 'Association').upper().replace(' ', '_')
                    edge_label = edge_data.get('label', '')
                    source_cardinality = edge_data.get('sourceCardinality', '1')
                    target_cardinality = edge_data.get('targetCardinality', '1')
                    
                    # Build edge properties
                    edge_props = {
                        'id': edge_id,
                        'relationship_type': edge_type,
                        'source_cardinality': source_cardinality,
                        'target_cardinality': target_cardinality,
                    }
                    
                    if edge_label:
                        edge_props['label'] = edge_label
                    
                    # Build property string
                    edge_prop_strings = []
                    for key, value in edge_props.items():
                        edge_prop_strings.append(f"{key}: {self._serialize_property(value)}")
                    
                    edge_props_clause = "{" + ", ".join(edge_prop_strings) + "}"
                    
                    # Create relationship query
                    # Use RELATES_TO as the relationship type in graph
                    rel_query = f"""
                    MATCH (source:Concept {{id: '{source_id}'}})
                    MATCH (target:Concept {{id: '{target_id}'}})
                    CREATE (source)-[r:RELATES_TO {edge_props_clause}]->(target)
                    RETURN r
                    """
                    
                    self.graph_client.query(graph_name, rel_query)
                    edges_created += 1
                    
                    logger.debug(
                        "Created edge in FalkorDB",
                        edge_id=edge_id,
                        source=source_id,
                        target=target_id,
                        type=edge_type
                    )
                    
                except Exception as edge_error:
                    logger.error(
                        "Failed to create edge",
                        edge_id=edge.get('id'),
                        error=str(edge_error)
                    )
                    continue
            
            # Create parent-child relationships for packages
            for node in nodes:
                try:
                    node_id = node.get('id', '')
                    node_data = node.get('data', {})
                    parent_id = node_data.get('parentId')
                    
                    if parent_id and parent_id in node_id_mapping:
                        # Create CONTAINS relationship from parent to child
                        contains_query = f"""
                        MATCH (parent:Concept {{id: '{parent_id}'}})
                        MATCH (child:Concept {{id: '{node_id}'}})
                        CREATE (parent)-[r:CONTAINS]->(child)
                        RETURN r
                        """
                        self.graph_client.query(graph_name, contains_query)
                        logger.debug(
                            "Created containment relationship",
                            parent=parent_id,
                            child=node_id
                        )
                except Exception as e:
                    logger.error(
                        "Failed to create containment relationship",
                        error=str(e)
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
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "graph_name": graph_name,
            }
    
    def get_graph_stats(self, graph_name: str) -> Dict[str, Any]:
        """Get statistics about a graph"""
        if not self.graph_client or not self.graph_client.is_connected():
            return {"error": "FalkorDB not available"}
        
        try:
            # Count nodes
            node_query = "MATCH (n:Concept) RETURN count(n) as count"
            node_result = self.graph_client.query(graph_name, node_query)
            total_nodes = node_result.result_set[0][0] if node_result.result_set else 0
            
            # Count edges
            edge_query = "MATCH ()-[r:RELATES_TO]->() RETURN count(r) as count"
            edge_result = self.graph_client.query(graph_name, edge_query)
            total_edges = edge_result.result_set[0][0] if edge_result.result_set else 0
            
            # Count containment relationships
            contains_query = "MATCH ()-[r:CONTAINS]->() RETURN count(r) as count"
            contains_result = self.graph_client.query(graph_name, contains_query)
            total_contains = contains_result.result_set[0][0] if contains_result.result_set else 0
            
            return {
                "total_nodes": total_nodes,
                "total_edges": total_edges,
                "total_contains": total_contains,
                "graph_name": graph_name,
            }
            
        except Exception as e:
            logger.error("Failed to get graph stats", graph_name=graph_name, error=str(e))
            return {"error": str(e)}