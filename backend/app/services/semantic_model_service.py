# backend/app/services/semantic_model_service.py
"""
Semantic Model Service - CORRECT GRAPH STRUCTURE
Path: backend/app/services/semantic_model_service.py

CORRECT APPROACH:
1. Attributes/Methods/Literals are PROPERTIES of the node (not separate nodes)
2. Edge relationship type is generic (RELATES_TO)
3. Actual relationship type (Association, Composition, etc.) is a PROPERTY
4. Edge label is the user-defined label (separate from relationship type)
"""

from typing import Any, Dict, List, Optional
import structlog
import json
from app.graph.client import get_graph_client

logger = structlog.get_logger()


class SemanticModelService:
    """Service for managing semantic models and FalkorDB synchronization"""
    
    def __init__(self):
        """Initialize service with FalkorDB client"""
        self.graph_client = get_graph_client()
    
    def _escape_string(self, value: str) -> str:
        """Escape special characters in strings for Cypher queries"""
        if not isinstance(value, str):
            return str(value)
        
        # Escape single quotes and backslashes
        escaped = value.replace("\\", "\\\\").replace("'", "\\'")
        return escaped
    
    def _serialize_property(self, value: Any) -> str:
        """
        Serialize a property value for Cypher query
        
        Args:
            value: Property value to serialize
            
        Returns:
            Serialized string ready for Cypher
        """
        if value is None:
            return "null"
        elif isinstance(value, str):
            return f"'{self._escape_string(value)}'"
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
        Sync diagram to FalkorDB with CORRECT graph structure
        
        CORRECT STRUCTURE:
        - Each concept is ONE node with all its attributes/methods as properties
        - Relationships use generic type (RELATES_TO) with relationship_type as property
        - Edge label is stored as 'label' property
        
        Args:
            graph_name: FalkorDB graph reference (format: username/workspace/diagram)
            nodes: List of diagram nodes with full data
            edges: List of diagram edges with relationship data
            
        Returns:
            Sync statistics and status
        """
        if not self.graph_client:
            logger.warning("FalkorDB client not available")
            return {"error": "FalkorDB client not initialized", "success": False}
        
        if not self.graph_client.is_connected():
            logger.warning("FalkorDB not connected - attempting reconnection")
            if not self.graph_client.connect():
                return {"error": "FalkorDB not connected", "success": False}
        
        try:
            logger.info(
                "🔄 Starting FalkorDB sync",
                graph_name=graph_name,
                node_count=len(nodes),
                edge_count=len(edges)
            )
            
            # Get graph object
            graph = self.graph_client.get_graph(graph_name)
            if not graph:
                error_msg = "Failed to get graph object"
                logger.error(error_msg, graph_name=graph_name)
                return {"error": error_msg, "success": False, "graph_name": graph_name}
            
            # Clear existing graph
            clear_query = "MATCH (n) DETACH DELETE n"
            graph.query(clear_query)
            logger.info("🗑️  Cleared existing graph", graph_name=graph_name)
            
            # Track created nodes
            nodes_created = 0
            node_id_mapping = {}
            
            # ================================================================
            # CREATE CONCEPT NODES WITH ALL PROPERTIES
            # ================================================================
            for node in nodes:
                try:
                    node_id = node.get('id', '')
                    node_type = node.get('type', 'Class')
                    node_data = node.get('data', {})
                    position = node.get('position', {})
                    
                    # Extract node name/label
                    node_label = node_data.get('label', node_data.get('name', 'Unnamed'))
                    
                    # Build ALL properties for this concept
                    properties = {
                        'id': node_id,
                        'name': node_label,
                        'label': node_label,
                        'node_type': node_type,
                        'x': position.get('x', 0),
                        'y': position.get('y', 0),
                    }
                    
                    # Add optional common properties
                    if 'color' in node_data:
                        properties['color'] = node_data['color']
                    if 'stereotype' in node_data and node_data['stereotype']:
                        properties['stereotype'] = node_data['stereotype']
                    if 'description' in node_data and node_data['description']:
                        properties['description'] = node_data['description']
                    
                    # Handle parentId for package containment
                    if 'parentId' in node_data and node_data['parentId']:
                        properties['parent_id'] = node_data['parentId']
                    
                    # ============================================================
                    # TYPE-SPECIFIC PROPERTIES (all as node properties, not separate nodes)
                    # ============================================================
                    
                    # PACKAGE properties
                    if node_type == 'package':
                        if 'isExpanded' in node_data:
                            properties['is_expanded'] = node_data['isExpanded']
                        if 'childCount' in node_data:
                            properties['child_count'] = node_data['childCount']
                    
                    # CLASS properties
                    elif node_type == 'class':
                        if 'isAbstract' in node_data:
                            properties['is_abstract'] = node_data['isAbstract']
                        
                        # Store attributes as JSON property
                        if 'attributes' in node_data and node_data['attributes']:
                            attrs = node_data['attributes']
                            properties['attributes'] = json.dumps(attrs)
                            properties['attribute_count'] = len(attrs)
                            
                            # Also store individual attribute properties for querying
                            for i, attr in enumerate(attrs):
                                properties[f'attr_{i}_name'] = attr.get('name', '')
                                properties[f'attr_{i}_type'] = attr.get('dataType', '')
                                if 'visibility' in attr:
                                    properties[f'attr_{i}_visibility'] = attr['visibility']
                                if 'key' in attr:
                                    properties[f'attr_{i}_key'] = attr['key']
                        
                        # Store methods as JSON property
                        if 'methods' in node_data and node_data['methods']:
                            methods = node_data['methods']
                            properties['methods'] = json.dumps(methods)
                            properties['method_count'] = len(methods)
                            
                            # Also store individual method properties for querying
                            for i, method in enumerate(methods):
                                properties[f'method_{i}_name'] = method.get('name', '')
                                properties[f'method_{i}_return_type'] = method.get('returnType', 'void')
                                if 'visibility' in method:
                                    properties[f'method_{i}_visibility'] = method['visibility']
                    
                    # OBJECT properties
                    elif node_type == 'object':
                        # Store attributes as JSON property
                        if 'attributes' in node_data and node_data['attributes']:
                            attrs = node_data['attributes']
                            properties['attributes'] = json.dumps(attrs)
                            properties['attribute_count'] = len(attrs)
                            
                            # Also store individual attribute properties
                            for i, attr in enumerate(attrs):
                                properties[f'attr_{i}_name'] = attr.get('name', '')
                                properties[f'attr_{i}_type'] = attr.get('dataType', '')
                    
                    # INTERFACE properties
                    elif node_type == 'interface':
                        # Store methods as JSON property
                        if 'methods' in node_data and node_data['methods']:
                            methods = node_data['methods']
                            properties['methods'] = json.dumps(methods)
                            properties['method_count'] = len(methods)
                            
                            # Also store individual method properties
                            for i, method in enumerate(methods):
                                properties[f'method_{i}_name'] = method.get('name', '')
                                properties[f'method_{i}_return_type'] = method.get('returnType', 'void')
                    
                    # ENUMERATION properties
                    elif node_type == 'enumeration':
                        # Store literals as JSON property
                        if 'literals' in node_data and node_data['literals']:
                            literals = node_data['literals']
                            properties['literals'] = json.dumps(literals)
                            properties['literal_count'] = len(literals)
                            
                            # Also store individual literals for querying
                            for i, literal in enumerate(literals):
                                properties[f'literal_{i}'] = literal
                    
                    # Build property string for Cypher
                    prop_strings = []
                    for key, value in properties.items():
                        prop_strings.append(f"{key}: {self._serialize_property(value)}")
                    
                    props_clause = "{" + ", ".join(prop_strings) + "}"
                    
                    # Use node type as primary label, add Concept as secondary
                    label = f"{node_type.upper()}:Concept"
                    
                    # Create concept node with ALL properties
                    create_query = f"CREATE (n:{label} {props_clause}) RETURN n"
                    graph.query(create_query)
                    nodes_created += 1
                    node_id_mapping[node_id] = True
                    
                    logger.debug(
                        "✅ Created concept node",
                        node_id=node_id,
                        node_type=node_type,
                        label=node_label,
                        property_count=len(properties)
                    )
                    
                except Exception as node_error:
                    logger.error(
                        "❌ Failed to create concept node",
                        node_id=node.get('id'),
                        error=str(node_error),
                        node_type=node.get('type')
                    )
                    continue
            
            # ================================================================
            # CREATE RELATIONSHIPS WITH PROPER STRUCTURE
            # ================================================================
            # Relationship type in Cypher: RELATES_TO (generic)
            # Actual type stored as property: relationship_type
            # User label stored as property: label
            # ================================================================
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
                            "⚠️  Skipping edge - missing nodes",
                            edge_id=edge_id,
                            source=source_id,
                            target=target_id
                        )
                        continue
                    
                    # Extract relationship properties
                    relationship_type = edge_data.get('type', 'Association')  # Association, Composition, etc.
                    edge_label = edge_data.get('label', '')  # User-defined label
                    source_cardinality = edge_data.get('sourceCardinality', '1')
                    target_cardinality = edge_data.get('targetCardinality', '1')
                    
                    # Build edge properties
                    edge_props = {
                        'id': edge_id,
                        'relationship_type': relationship_type,  # Association, Composition, etc.
                        'source_cardinality': source_cardinality,
                        'target_cardinality': target_cardinality,
                    }
                    
                    # Add user-defined label if provided
                    if edge_label:
                        edge_props['label'] = edge_label
                    
                    # Add optional properties
                    if 'color' in edge_data:
                        edge_props['color'] = edge_data['color']
                    if 'strokeWidth' in edge_data:
                        edge_props['stroke_width'] = edge_data['strokeWidth']
                    if 'isIdentifying' in edge_data:
                        edge_props['is_identifying'] = edge_data['isIdentifying']
                    
                    # Build property string
                    edge_prop_strings = []
                    for key, value in edge_props.items():
                        edge_prop_strings.append(f"{key}: {self._serialize_property(value)}")
                    
                    edge_props_clause = "{" + ", ".join(edge_prop_strings) + "}"
                    
                    # CRITICAL: Use generic RELATES_TO type, store actual type as property
                    create_edge_query = f"""
                    MATCH (source:Concept {{id: {self._serialize_property(source_id)}}})
                    MATCH (target:Concept {{id: {self._serialize_property(target_id)}}})
                    CREATE (source)-[r:RELATES_TO {edge_props_clause}]->(target)
                    RETURN r
                    """
                    
                    graph.query(create_edge_query)
                    edges_created += 1
                    
                    logger.debug(
                        "✅ Created relationship",
                        edge_id=edge_id,
                        relationship_type=relationship_type,
                        label=edge_label,
                        source=source_id,
                        target=target_id
                    )
                    
                except Exception as edge_error:
                    logger.error(
                        "❌ Failed to create relationship",
                        edge_id=edge.get('id'),
                        error=str(edge_error)
                    )
                    continue
            
            # ================================================================
            # CREATE PACKAGE CONTAINMENT RELATIONSHIPS
            # ================================================================
            contains_created = 0
            for node in nodes:
                try:
                    node_id = node.get('id', '')
                    node_data = node.get('data', {})
                    parent_id = node_data.get('parentId')
                    
                    if parent_id and parent_id in node_id_mapping:
                        # Create CONTAINS relationship
                        contains_query = f"""
                        MATCH (parent:Concept {{id: {self._serialize_property(parent_id)}}})
                        MATCH (child:Concept {{id: {self._serialize_property(node_id)}}})
                        CREATE (parent)-[r:CONTAINS]->(child)
                        RETURN r
                        """
                        
                        graph.query(contains_query)
                        contains_created += 1
                        
                except Exception as e:
                    logger.error(
                        "❌ Failed to create containment relationship",
                        node_id=node.get('id'),
                        error=str(e)
                    )
                    continue
            
            logger.info(
                "✅ FalkorDB sync completed successfully",
                graph_name=graph_name,
                nodes_created=nodes_created,
                edges_created=edges_created,
                contains_created=contains_created
            )
            
            return {
                "success": True,
                "graph_name": graph_name,
                "nodes_created": nodes_created,
                "edges_created": edges_created,
                "contains_created": contains_created,
            }
            
        except Exception as e:
            logger.error(
                "❌ FalkorDB sync failed",
                graph_name=graph_name,
                error=str(e),
                error_type=type(e).__name__
            )
            import traceback
            logger.error("Full traceback:", traceback=traceback.format_exc())
            
            return {
                "success": False,
                "error": str(e),
                "graph_name": graph_name,
            }
    
    def get_graph_stats(self, graph_name: str) -> Dict[str, Any]:
        """Get comprehensive statistics about a graph"""
        if not self.graph_client or not self.graph_client.is_connected():
            return {"error": "FalkorDB not available", "success": False}
        
        try:
            graph = self.graph_client.get_graph(graph_name)
            if not graph:
                return {"error": "Failed to get graph", "success": False}
            
            # Count concept nodes
            node_query = "MATCH (n:Concept) RETURN count(n) as count"
            node_result = graph.query(node_query)
            total_nodes = node_result.result_set[0][0] if node_result.result_set else 0
            
            # Count relationships
            edge_query = "MATCH ()-[r:RELATES_TO]->() RETURN count(r) as count"
            edge_result = graph.query(edge_query)
            total_edges = edge_result.result_set[0][0] if edge_result.result_set else 0
            
            # Count containment relationships
            contains_query = "MATCH ()-[r:CONTAINS]->() RETURN count(r) as count"
            contains_result = graph.query(contains_query)
            total_contains = contains_result.result_set[0][0] if contains_result.result_set else 0
            
            # Count by node type
            type_counts = {}
            for node_type in ['PACKAGE', 'CLASS', 'OBJECT', 'INTERFACE', 'ENUMERATION']:
                type_query = f"MATCH (n:{node_type}) RETURN count(n) as count"
                type_result = graph.query(type_query)
                count = type_result.result_set[0][0] if type_result.result_set else 0
                type_counts[node_type.lower()] = count
            
            # Count total attributes and methods across all nodes
            total_attributes = 0
            total_methods = 0
            stats_query = "MATCH (n:Concept) WHERE n.attribute_count IS NOT NULL OR n.method_count IS NOT NULL RETURN n.attribute_count, n.method_count"
            stats_result = graph.query(stats_query)
            if stats_result.result_set:
                for row in stats_result.result_set:
                    if row[0] is not None:
                        total_attributes += row[0]
                    if row[1] is not None:
                        total_methods += row[1]
            
            return {
                "success": True,
                "graph_name": graph_name,
                "total_concepts": total_nodes,
                "total_relationships": total_edges,
                "total_contains": total_contains,
                "total_attributes": total_attributes,
                "total_methods": total_methods,
                "concept_types": type_counts,
            }
            
        except Exception as e:
            logger.error("Failed to get graph stats", graph_name=graph_name, error=str(e))
            return {"error": str(e), "success": False}
    
    def query_graph(self, graph_name: str, cypher_query: str) -> Dict[str, Any]:
        """Execute a Cypher query on the graph"""
        if not self.graph_client or not self.graph_client.is_connected():
            return {"error": "FalkorDB not available", "success": False}
        
        try:
            graph = self.graph_client.get_graph(graph_name)
            if not graph:
                return {"error": "Failed to get graph", "success": False}
            
            result = graph.query(cypher_query)
            
            # Convert result to dictionary format
            if result.result_set:
                return {
                    "success": True,
                    "results": [list(row) for row in result.result_set],
                    "statistics": result.statistics if hasattr(result, 'statistics') else {}
                }
            else:
                return {
                    "success": True,
                    "results": [],
                    "statistics": result.statistics if hasattr(result, 'statistics') else {}
                }
                
        except Exception as e:
            logger.error("Query failed", graph_name=graph_name, error=str(e))
            return {"error": str(e), "success": False}