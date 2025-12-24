"""
FalkorDB Graph Database Client
Compatible with FalkorDB 1.2.2+
"""

from typing import Any, Dict, List, Optional
from functools import lru_cache
import structlog
from falkordb import FalkorDB

from app.core.config import settings

logger = structlog.get_logger(__name__)


class GraphClient:
    """
    Wrapper for FalkorDB operations
    Compatible with FalkorDB 1.2.2 and redis-py 7.1+
    """
    
    def __init__(self):
        """Initialize FalkorDB connection"""
        self.host = settings.FALKORDB_HOST
        self.port = settings.FALKORDB_PORT
        self.graph_name = settings.FALKORDB_GRAPH
        self.password = settings.FALKORDB_PASSWORD
        
        self._client = None
        self._graph = None
    
    def connect(self) -> None:
        """Establish connection to FalkorDB"""
        try:
            # Create FalkorDB client with password if provided
            connection_params = {
                'host': self.host,
                'port': self.port,
            }
            
            if self.password:
                connection_params['password'] = self.password
            
            self._client = FalkorDB(**connection_params)
            
            # Select graph
            self._graph = self._client.select_graph(self.graph_name)
            
            logger.info(
                "Connected to FalkorDB",
                host=self.host,
                port=self.port,
                graph=self.graph_name,
            )
        except Exception as e:
            logger.error("Failed to connect to FalkorDB", error=str(e))
            raise
    
    def query(
        self,
        cypher_query: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Execute a Cypher query
        
        Args:
            cypher_query: Cypher query string
            params: Query parameters
            
        Returns:
            List of result records as dictionaries
        """
        if not self._graph:
            self.connect()
        
        try:
            # Execute query
            result = self._graph.query(cypher_query, params or {})
            
            # Convert result to list of dictionaries
            records = []
            if result.result_set:
                for record in result.result_set:
                    record_dict = {}
                    for i, value in enumerate(record):
                        # Get column name from result header
                        if i < len(result.header):
                            column_name = result.header[i][1]
                            record_dict[column_name] = self._serialize_value(value)
                    records.append(record_dict)
            
            logger.debug(
                "Query executed",
                query=cypher_query[:100],
                params=params,
                result_count=len(records),
            )
            
            return records
            
        except Exception as e:
            logger.error(
                "Query execution failed",
                query=cypher_query,
                error=str(e),
            )
            raise
    
    def execute(
        self,
        cypher_query: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute a write query (CREATE, UPDATE, DELETE)
        
        Returns:
            Statistics about the execution
        """
        if not self._graph:
            self.connect()
        
        try:
            result = self._graph.query(cypher_query, params or {})
            
            stats = {
                "nodes_created": result.nodes_created,
                "nodes_deleted": result.nodes_deleted,
                "relationships_created": result.relationships_created,
                "relationships_deleted": result.relationships_deleted,
                "properties_set": result.properties_set,
            }
            
            logger.debug(
                "Write query executed",
                query=cypher_query[:100],
                stats=stats,
            )
            
            return stats
            
        except Exception as e:
            logger.error(
                "Write query failed",
                query=cypher_query,
                error=str(e),
            )
            raise
    
    def _serialize_value(self, value: Any) -> Any:
        """
        Serialize graph values to JSON-compatible types
        """
        if hasattr(value, '__dict__'):
            # Node or Relationship object
            result = dict(value.__dict__)
            # Remove internal attributes
            result = {k: v for k, v in result.items() if not k.startswith('_')}
            return result
        elif isinstance(value, (list, tuple)):
            return [self._serialize_value(v) for v in value]
        elif isinstance(value, dict):
            return {k: self._serialize_value(v) for k, v in value.items()}
        else:
            return value
    
    def close(self) -> None:
        """Close connection to FalkorDB"""
        if self._client:
            self._client.close()
            logger.info("FalkorDB connection closed")


@lru_cache()
def get_graph_client() -> GraphClient:
    """
    Get singleton graph client instance
    """
    client = GraphClient()
    client.connect()
    return client