# backend/app/graph/client.py
"""
FalkorDB Graph Database Client - COMPLETE WORKING VERSION
Path: backend/app/graph/client.py
"""
from typing import Any, Dict, List, Optional
import structlog
from datetime import datetime

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
    
    def create_concept(
        self,
        graph_name: str,
        concept_id: str,
        concept_type: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Create a concept node"""
        if not self.is_connected():
            return False
        
        props = properties or {}
        props["id"] = concept_id
        props["type"] = concept_type
        props["created_at"] = datetime.utcnow().isoformat()
        
        prop_strings = [f"{k}: ${k}" for k in props.keys()]
        prop_clause = "{" + ", ".join(prop_strings) + "}"
        query = f"CREATE (c:Concept {prop_clause}) RETURN c"
        
        try:
            result = self.execute_query(graph_name, query, props)
            if result:
                logger.info("Concept created", graph_name=graph_name, concept_id=concept_id)
                return True
            return False
        except Exception as e:
            logger.error("Failed to create concept", error=str(e))
            return False
    
    def update_concept(
        self,
        graph_name: str,
        concept_id: str,
        properties: Dict[str, Any]
    ) -> bool:
        """Update concept properties"""
        if not self.is_connected() or not properties:
            return False
        
        params = {"id": concept_id, "updated_at": datetime.utcnow().isoformat()}
        set_clauses = ["c.updated_at = $updated_at"]
        
        for key, value in properties.items():
            if key not in ["id", "created_at"]:
                param_name = f"prop_{key}"
                set_clauses.append(f"c.{key} = ${param_name}")
                params[param_name] = value
        
        query = f"""
        MATCH (c:Concept {{id: $id}})
        SET {', '.join(set_clauses)}
        RETURN c
        """
        
        try:
            result = self.execute_query(graph_name, query, params)
            return bool(result)
        except Exception as e:
            logger.error("Failed to update concept", error=str(e))
            return False
    
    def create_relationship(
        self,
        graph_name: str,
        from_id: str,
        to_id: str,
        rel_type: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Create a relationship between concepts"""
        if not self.is_connected():
            return False
        
        props = properties or {}
        props["created_at"] = datetime.utcnow().isoformat()
        
        rel_type = rel_type.replace(" ", "_").replace("-", "_").upper()
        
        prop_strings = [f"{k}: ${k}" for k in props.keys()]
        prop_clause = "{" + ", ".join(prop_strings) + "}" if props else ""
        
        query = f"""
        MATCH (from:Concept {{id: $from_id}})
        MATCH (to:Concept {{id: $to_id}})
        CREATE (from)-[r:{rel_type} {prop_clause}]->(to)
        RETURN r
        """
        
        params = {"from_id": from_id, "to_id": to_id, **props}
        
        try:
            result = self.execute_query(graph_name, query, params)
            if result:
                logger.info("Relationship created", from_id=from_id, to_id=to_id, rel_type=rel_type)
                return True
            return False
        except Exception as e:
            logger.error("Failed to create relationship", error=str(e))
            return False
    
    def delete_concept(self, graph_name: str, concept_id: str) -> bool:
        """Delete a concept and relationships"""
        if not self.is_connected():
            return False
        
        query = "MATCH (c:Concept {id: $id}) DETACH DELETE c"
        
        try:
            self.execute_query(graph_name, query, {"id": concept_id})
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