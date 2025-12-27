# backend/app/graph/client.py
"""
FalkorDB Graph Database Client - FIXED
Manages connections and operations with FalkorDB graph database
"""
from typing import Any, Dict, List, Optional
import structlog
from redis.exceptions import ConnectionError as RedisConnectionError

logger = structlog.get_logger()


class GraphClient:
    """FalkorDB client for managing semantic models"""
    
    def __init__(self):
        self._client: Optional[Any] = None
        self._graphs: Dict[str, Any] = {}
        self._connected = False
        
    def connect(self) -> bool:
        """
        Establish connection to FalkorDB
        
        Returns:
            True if connected successfully, False otherwise
        """
        try:
            from falkordb import FalkorDB
            from app.core.config import settings
            
            self._client = FalkorDB(
                host=settings.FALKORDB_HOST,
                port=settings.FALKORDB_PORT,
                password=settings.FALKORDB_PASSWORD if settings.FALKORDB_PASSWORD else None
            )
            
            # Test connection by executing a simple query
            test_graph = self._client.select_graph("__test__")
            test_graph.query("RETURN 1")
            
            self._connected = True
            logger.info(
                "Connected to FalkorDB successfully",
                host=settings.FALKORDB_HOST,
                port=settings.FALKORDB_PORT
            )
            return True
            
        except RedisConnectionError as e:
            self._connected = False
            logger.warning(
                "Failed to connect to FalkorDB - Redis connection error",
                host=getattr(settings, 'FALKORDB_HOST', 'unknown'),
                port=getattr(settings, 'FALKORDB_PORT', 'unknown'),
                error=str(e)
            )
            return False
        except ImportError as e:
            self._connected = False
            logger.error("FalkorDB library not installed", error=str(e))
            return False
        except Exception as e:
            self._connected = False
            logger.error("Failed to connect to FalkorDB", error=str(e), exc_info=True)
            return False
    
    def is_connected(self) -> bool:
        """Check if client is connected"""
        return self._connected and self._client is not None
    
    def get_graph(self, graph_name: str) -> Optional[Any]:
        """
        Get or create a graph by name
        
        Args:
            graph_name: Name of the graph (typically user_id_model_id)
            
        Returns:
            Graph instance or None if not connected
        """
        if not self.is_connected():
            logger.warning("Cannot get graph - not connected to FalkorDB")
            return None
            
        try:
            if graph_name not in self._graphs:
                self._graphs[graph_name] = self._client.select_graph(graph_name)
                logger.info("Graph selected", graph_name=graph_name)
                
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
        """
        Execute a Cypher query
        
        Args:
            graph_name: Name of the graph
            query: Cypher query string
            params: Query parameters
            
        Returns:
            List of result records
        """
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
            
            # Convert result to list of dictionaries
            records = []
            if result.result_set:
                for record in result.result_set:
                    record_dict = {}
                    for i, column in enumerate(result.header):
                        record_dict[column[1]] = record[i]
                    records.append(record_dict)
            
            logger.debug(
                "Query executed successfully",
                graph_name=graph_name,
                record_count=len(records)
            )
            
            return records
            
        except Exception as e:
            logger.error(
                "Failed to execute query",
                graph_name=graph_name,
                query=query[:100],
                error=str(e),
                exc_info=True
            )
            return []
    
    def create_concept(
        self,
        graph_name: str,
        concept_id: str,
        concept_type: str,
        properties: Dict[str, Any]
    ) -> bool:
        """Create a new concept in the graph"""
        if not self.is_connected():
            logger.warning("Cannot create concept - not connected to FalkorDB")
            return False
        
        # Build properties string for Cypher
        props = {k: v for k, v in properties.items() if v is not None}
        props["id"] = concept_id
        props["kind"] = concept_type
        
        query = """
        CREATE (c:Concept $props)
        RETURN c
        """
        
        try:
            result = self.execute_query(graph_name, query, {"props": props})
            if result:
                logger.info(
                    "Concept created",
                    graph_name=graph_name,
                    concept_id=concept_id,
                    concept_type=concept_type
                )
                return True
            return False
        except Exception as e:
            logger.error(
                "Failed to create concept",
                concept_id=concept_id,
                error=str(e)
            )
            return False
    
    def update_concept(
        self,
        graph_name: str,
        concept_id: str,
        properties: Dict[str, Any]
    ) -> bool:
        """Update an existing concept"""
        if not self.is_connected():
            logger.warning("Cannot update concept - not connected to FalkorDB")
            return False
        
        # Build SET clause for properties
        set_clauses = []
        params = {"id": concept_id}
        
        for key, value in properties.items():
            if value is not None:
                param_name = f"val_{key}"
                set_clauses.append(f"c.{key} = ${param_name}")
                params[param_name] = value
        
        if not set_clauses:
            logger.debug("No properties to update", concept_id=concept_id)
            return True
        
        query = f"""
        MATCH (c:Concept {{id: $id}})
        SET {', '.join(set_clauses)}
        RETURN c
        """
        
        try:
            result = self.execute_query(graph_name, query, params)
            if result:
                logger.debug(
                    "Concept updated",
                    graph_name=graph_name,
                    concept_id=concept_id
                )
                return True
            return False
        except Exception as e:
            logger.error(
                "Failed to update concept",
                concept_id=concept_id,
                error=str(e)
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
        """Create a relationship between two concepts"""
        if not self.is_connected():
            logger.warning("Cannot create relationship - not connected to FalkorDB")
            return False
        
        props = properties or {}
        
        query = f"""
        MATCH (from:Concept {{id: $from_id}})
        MATCH (to:Concept {{id: $to_id}})
        CREATE (from)-[r:{rel_type} $props]->(to)
        RETURN r
        """
        
        params = {
            "from_id": from_id,
            "to_id": to_id,
            "props": props
        }
        
        try:
            result = self.execute_query(graph_name, query, params)
            if result:
                logger.info(
                    "Relationship created",
                    graph_name=graph_name,
                    from_id=from_id,
                    to_id=to_id,
                    rel_type=rel_type
                )
                return True
            return False
        except Exception as e:
            logger.error(
                "Failed to create relationship",
                from_id=from_id,
                to_id=to_id,
                rel_type=rel_type,
                error=str(e)
            )
            return False
    
    def delete_concept(self, graph_name: str, concept_id: str) -> bool:
        """Delete a concept and all its relationships"""
        if not self.is_connected():
            logger.warning("Cannot delete concept - not connected to FalkorDB")
            return False
        
        query = """
        MATCH (c:Concept {id: $id})
        DETACH DELETE c
        """
        
        params = {"id": concept_id}
        
        try:
            self.execute_query(graph_name, query, params)
            logger.info("Concept deleted", graph_name=graph_name, concept_id=concept_id)
            return True
        except Exception as e:
            logger.error("Failed to delete concept", concept_id=concept_id, error=str(e))
            return False
    
    def delete_graph(self, graph_name: str) -> bool:
        """Delete an entire graph"""
        if not self.is_connected():
            logger.warning("Cannot delete graph - not connected to FalkorDB")
            return False
        
        try:
            if graph_name in self._graphs:
                del self._graphs[graph_name]
            
            if self._client:
                self._client.delete(graph_name)
                logger.info("Graph deleted", graph_name=graph_name)
            
            return True
        except Exception as e:
            logger.error("Failed to delete graph", graph_name=graph_name, error=str(e))
            return False
    
    def close(self) -> None:
        """Close all connections"""
        if self._client:
            self._graphs.clear()
            self._client = None
            self._connected = False
            logger.info("FalkorDB connections closed")


# Global graph client instance
_graph_client: Optional[GraphClient] = None


def get_graph_client() -> GraphClient:
    """
    Get or create global graph client instance
    
    Returns:
        GraphClient instance (may not be connected if FalkorDB is unavailable)
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