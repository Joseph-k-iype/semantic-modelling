# backend/app/graph/client.py
"""
FalkorDB Graph Database Client - COMPLETE IMPLEMENTATION
Path: backend/app/graph/client.py

CRITICAL FIXES:
1. Support creating nodes with custom labels (Entity, Class, Task, etc.)
2. Properly handle multi-label nodes (Entity:Concept, Class:Concept)
3. Support typed relationships (RELATES_TO, EXTENDS, etc.)
4. Handle JSON serialization for complex properties
"""
from typing import Any, Dict, List, Optional
import structlog
from datetime import datetime
import json

logger = structlog.get_logger(__name__)


class GraphClient:
    """FalkorDB client for managing semantic models"""
    
    def __init__(self):
        """Initialize graph client"""
        self._client: Optional[Any] = None
        self._graphs: Dict[str, Any] = {}
        self._connected = False
        self._connection_error: Optional[str] = None
        
    def connect(self) -> bool:
        """
        Establish connection to FalkorDB
        
        Returns:
            True if connected successfully, False otherwise
        """
        try:
            from falkordb import FalkorDB
            from app.core.config import settings
            
            # Create FalkorDB client
            self._client = FalkorDB(
                host=settings.FALKORDB_HOST,
                port=settings.FALKORDB_PORT,
                password=settings.FALKORDB_PASSWORD if settings.FALKORDB_PASSWORD else None
            )
            
            # Test connection
            test_graph = self._client.select_graph("__connection_test__")
            test_graph.query("RETURN 1 AS test")
            
            # Clean up test graph
            try:
                self._client.delete("__connection_test__")
            except:
                pass
            
            self._connected = True
            self._connection_error = None
            
            logger.info(
                "✅ Connected to FalkorDB successfully",
                host=settings.FALKORDB_HOST,
                port=settings.FALKORDB_PORT
            )
            return True
            
        except ImportError as e:
            self._connected = False
            self._connection_error = f"FalkorDB library not installed: {str(e)}"
            logger.error(
                "❌ FalkorDB library not installed",
                error=str(e),
                hint="Install with: pip install falkordb"
            )
            return False
            
        except Exception as e:
            self._connected = False
            self._connection_error = f"Connection error: {str(e)}"
            logger.warning(
                "⚠️  Failed to connect to FalkorDB - graph features will be disabled",
                error=str(e),
                error_type=type(e).__name__
            )
            return False
    
    def is_connected(self) -> bool:
        """Check if client is connected"""
        return self._connected and self._client is not None
    
    def get_connection_error(self) -> Optional[str]:
        """Get the last connection error message"""
        return self._connection_error
    
    def get_graph(self, graph_name: str) -> Optional[Any]:
        """Get or create a graph by name"""
        if not self.is_connected():
            logger.warning("Cannot get graph - not connected to FalkorDB")
            return None
            
        try:
            if graph_name not in self._graphs:
                self._graphs[graph_name] = self._client.select_graph(graph_name)
                logger.debug("Graph selected", graph_name=graph_name)
                
            return self._graphs[graph_name]
            
        except Exception as e:
            logger.error("Failed to get graph", graph_name=graph_name, error=str(e))
            return None
    
    def execute_query(
        self,
        graph_name: str,
        query: str,
        params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Execute a Cypher query"""
        if not self.is_connected():
            logger.warning("Cannot execute query - not connected to FalkorDB")
            return []
        
        graph = self.get_graph(graph_name)
        if not graph:
            logger.error("Failed to get graph for query execution", graph_name=graph_name)
            return []
        
        try:
            logger.debug(
                "Executing query",
                graph_name=graph_name,
                query=query[:100] + "..." if len(query) > 100 else query,
                params=params
            )
            
            result = graph.query(query, params or {})
            
            records = []
            if result.result_set:
                for record in result.result_set:
                    record_dict = {}
                    for i, column in enumerate(result.header):
                        column_name = column[1] if len(column) > 1 else f"col_{i}"
                        record_dict[column_name] = record[i]
                    records.append(record_dict)
            
            logger.debug("Query executed successfully", graph_name=graph_name, result_count=len(records))
            return records
            
        except Exception as e:
            logger.error("Failed to execute query", graph_name=graph_name, error=str(e))
            return []
    
    def _serialize_property_value(self, value: Any) -> Any:
        """
        Serialize property value for FalkorDB
        
        Handles complex types like lists, dicts, etc.
        """
        if value is None:
            return ""
        elif isinstance(value, (str, int, float, bool)):
            return value
        elif isinstance(value, (list, dict)):
            # FalkorDB doesn't natively support complex types, so we JSON serialize
            return json.dumps(value)
        elif isinstance(value, datetime):
            return value.isoformat()
        else:
            return str(value)
    
    def create_concept(
        self,
        graph_name: str,
        concept_id: str,
        concept_type: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Create a concept node with custom label
        
        CRITICAL FIX: Now supports custom labels like Entity, Class, Task, etc.
        Creates multi-label nodes: Entity:Concept, Class:Concept, etc.
        
        Args:
            graph_name: Name of the graph
            concept_id: Unique identifier for the concept
            concept_type: Type/label for the node (Entity, Class, Task, etc.)
            properties: Additional properties for the node
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected():
            return False
        
        props = properties or {}
        
        # Add core properties
        props["id"] = concept_id
        props["type"] = concept_type
        props["created_at"] = datetime.utcnow().isoformat()
        
        # Serialize complex properties
        serialized_props = {
            k: self._serialize_property_value(v) 
            for k, v in props.items()
        }
        
        # Build property clause
        prop_strings = []
        for k, v in serialized_props.items():
            if isinstance(v, str):
                # Escape quotes in strings
                escaped_value = v.replace("'", "\\'")
                prop_strings.append(f"{k}: '{escaped_value}'")
            elif isinstance(v, bool):
                prop_strings.append(f"{k}: {str(v).lower()}")
            elif v is None or v == "":
                prop_strings.append(f"{k}: ''")
            else:
                prop_strings.append(f"{k}: {v}")
        
        prop_clause = "{" + ", ".join(prop_strings) + "}" if prop_strings else ""
        
        # CRITICAL FIX: Use custom label AND add Concept as secondary label
        # This creates nodes like: (c:Entity:Concept) or (c:Class:Concept)
        # This allows filtering by specific type OR all concepts
        labels = f"{concept_type}:Concept"
        query = f"CREATE (c:{labels} {prop_clause}) RETURN c"
        
        try:
            result = self.execute_query(graph_name, query, {})
            if result:
                logger.info(
                    "Concept created",
                    graph_name=graph_name,
                    concept_id=concept_id,
                    concept_type=concept_type,
                    labels=labels
                )
                return True
            return False
        except Exception as e:
            logger.error(
                "Failed to create concept",
                error=str(e),
                concept_id=concept_id,
                concept_type=concept_type
            )
            return False
    
    def update_concept(
        self,
        graph_name: str,
        concept_id: str,
        properties: Dict[str, Any]
    ) -> bool:
        """
        Update concept properties
        
        CRITICAL FIX: Properly handles JSON serialization for complex properties
        """
        if not self.is_connected() or not properties:
            return False
        
        # Serialize complex properties
        serialized_props = {
            k: self._serialize_property_value(v) 
            for k, v in properties.items()
            if k not in ["id", "created_at"]  # Don't update these
        }
        
        # Build SET clauses
        set_clauses = ["c.updated_at = '" + datetime.utcnow().isoformat() + "'"]
        
        for key, value in serialized_props.items():
            if isinstance(value, str):
                # Escape quotes in strings
                escaped_value = value.replace("'", "\\'")
                set_clauses.append(f"c.{key} = '{escaped_value}'")
            elif isinstance(value, bool):
                set_clauses.append(f"c.{key} = {str(value).lower()}")
            elif value is None or value == "":
                set_clauses.append(f"c.{key} = ''")
            else:
                set_clauses.append(f"c.{key} = {value}")
        
        query = f"""
        MATCH (c {{id: '{concept_id}'}})
        SET {', '.join(set_clauses)}
        RETURN c
        """
        
        try:
            result = self.execute_query(graph_name, query, {})
            if result:
                logger.info(
                    "Concept updated",
                    graph_name=graph_name,
                    concept_id=concept_id,
                    updated_fields=list(serialized_props.keys())
                )
            return bool(result)
        except Exception as e:
            logger.error(
                "Failed to update concept",
                error=str(e),
                concept_id=concept_id
            )
            return False
    
    def create_relationship(
        self,
        graph_name: str,
        from_id: str,
        to_id: str,
        rel_type: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Create a relationship between concepts
        
        CRITICAL FIX: Supports custom relationship types (RELATES_TO, EXTENDS, etc.)
        Properly handles relationship properties including cardinality
        """
        if not self.is_connected():
            return False
        
        props = properties or {}
        props["created_at"] = datetime.utcnow().isoformat()
        
        # Serialize complex properties
        serialized_props = {
            k: self._serialize_property_value(v) 
            for k, v in props.items()
        }
        
        # Clean relationship type (uppercase, replace spaces/dashes with underscores)
        clean_rel_type = rel_type.replace(" ", "_").replace("-", "_").upper()
        
        # Build property clause
        prop_strings = []
        for k, v in serialized_props.items():
            if isinstance(v, str):
                escaped_value = v.replace("'", "\\'")
                prop_strings.append(f"{k}: '{escaped_value}'")
            elif isinstance(v, bool):
                prop_strings.append(f"{k}: {str(v).lower()}")
            elif v is None or v == "":
                prop_strings.append(f"{k}: ''")
            else:
                prop_strings.append(f"{k}: {v}")
        
        prop_clause = "{" + ", ".join(prop_strings) + "}" if prop_strings else ""
        
        # CRITICAL FIX: Use MERGE instead of CREATE to avoid duplicates
        # Match both nodes first, then create relationship
        query = f"""
        MATCH (from {{id: '{from_id}'}})
        MATCH (to {{id: '{to_id}'}})
        MERGE (from)-[r:{clean_rel_type} {prop_clause}]->(to)
        RETURN r
        """
        
        try:
            result = self.execute_query(graph_name, query, {})
            if result:
                logger.info(
                    "Relationship created",
                    graph_name=graph_name,
                    from_id=from_id,
                    to_id=to_id,
                    rel_type=clean_rel_type,
                    properties=serialized_props
                )
                return True
            return False
        except Exception as e:
            logger.error(
                "Failed to create relationship",
                error=str(e),
                from_id=from_id,
                to_id=to_id,
                rel_type=clean_rel_type
            )
            return False
    
    def get_concept(
        self,
        graph_name: str,
        concept_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get a concept by ID"""
        if not self.is_connected():
            return None
        
        query = f"MATCH (c {{id: '{concept_id}'}}) RETURN c"
        
        try:
            results = self.execute_query(graph_name, query, {})
            if results and len(results) > 0:
                return results[0]
            return None
        except Exception as e:
            logger.error("Failed to get concept", error=str(e))
            return None
    
    def get_relationships(
        self,
        graph_name: str,
        concept_id: str,
        direction: str = "both"
    ) -> List[Dict[str, Any]]:
        """Get relationships for a concept"""
        if not self.is_connected():
            return []
        
        if direction == "outgoing":
            query = f"""
            MATCH (c {{id: '{concept_id}'}})-[r]->(related)
            RETURN r, related
            """
        elif direction == "incoming":
            query = f"""
            MATCH (c {{id: '{concept_id}'}})<-[r]-(related)
            RETURN r, related
            """
        else:  # both
            query = f"""
            MATCH (c {{id: '{concept_id}'}})-[r]-(related)
            RETURN r, related
            """
        
        try:
            results = self.execute_query(graph_name, query, {})
            return results or []
        except Exception as e:
            logger.error("Failed to get relationships", error=str(e))
            return []
    
    def delete_concept(self, graph_name: str, concept_id: str) -> bool:
        """Delete a concept and its relationships"""
        if not self.is_connected():
            return False
        
        query = f"MATCH (c {{id: '{concept_id}'}}) DETACH DELETE c"
        
        try:
            self.execute_query(graph_name, query, {})
            logger.info("Concept deleted", concept_id=concept_id)
            return True
        except Exception as e:
            logger.error("Failed to delete concept", error=str(e))
            return False
    
    def delete_graph(self, graph_name: str) -> bool:
        """Delete an entire graph"""
        if not self.is_connected():
            return False
        
        try:
            if graph_name in self._graphs:
                del self._graphs[graph_name]
            
            if self._client:
                self._client.delete(graph_name)
                logger.info("Graph deleted", graph_name=graph_name)
            
            return True
        except Exception as e:
            logger.error("Failed to delete graph", error=str(e))
            return False
    
    def close(self) -> None:
        """Close all connections"""
        if self._client:
            self._graphs.clear()
            self._client = None
            self._connected = False
            self._connection_error = None
            logger.info("FalkorDB connections closed")


# Global client instance
_graph_client: Optional[GraphClient] = None


def get_graph_client() -> GraphClient:
    """
    Get or create global graph client instance
    
    Returns:
        GraphClient instance (may not be connected if FalkorDB unavailable)
    """
    global _graph_client
    
    if _graph_client is None:
        _graph_client = GraphClient()
        _graph_client.connect()
    
    return _graph_client


def close_graph_client() -> None:
    """Close global graph client"""
    global _graph_client
    
    if _graph_client:
        _graph_client.close()
        _graph_client = None


def reset_graph_client() -> GraphClient:
    """Reset and recreate global graph client"""
    close_graph_client()
    return get_graph_client()