# backend/app/graph/client.py
"""
FalkorDB Graph Database Client
Manages connections and operations with FalkorDB graph database
"""
from typing import Any, Dict, List, Optional
from falkordb import FalkorDB, Graph
from app.core.config import settings  # FIXED: Use singleton settings instead of get_settings()
import structlog

logger = structlog.get_logger()


class GraphClient:
    """FalkorDB client for managing semantic models"""
    
    def __init__(self):
        self._client: Optional[FalkorDB] = None
        self._graphs: Dict[str, Graph] = {}
        
    def connect(self) -> None:
        """Establish connection to FalkorDB"""
        try:
            self._client = FalkorDB(
                host=settings.FALKORDB_HOST,
                port=settings.FALKORDB_PORT,
                password=settings.FALKORDB_PASSWORD
            )
            logger.info(
                "Connected to FalkorDB",
                host=settings.FALKORDB_HOST,
                port=settings.FALKORDB_PORT
            )
        except Exception as e:
            logger.error("Failed to connect to FalkorDB", error=str(e))
            raise
    
    def get_graph(self, graph_name: str) -> Graph:
        """
        Get or create a graph by name
        
        Args:
            graph_name: Name of the graph (typically user_id_model_id)
            
        Returns:
            Graph instance
        """
        if not self._client:
            self.connect()
            
        if graph_name not in self._graphs:
            self._graphs[graph_name] = self._client.select_graph(graph_name)
            logger.info("Graph selected", graph_name=graph_name)
            
        return self._graphs[graph_name]
    
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
        graph = self.get_graph(graph_name)
        
        try:
            result = graph.query(query, params or {})
            
            # Convert result to list of dictionaries
            records = []
            if result.result_set:
                for record in result.result_set:
                    records.append(dict(zip(result.header, record)))
            
            logger.debug(
                "Query executed",
                graph=graph_name,
                query=query,
                records_count=len(records)
            )
            
            return records
            
        except Exception as e:
            logger.error(
                "Query execution failed",
                graph=graph_name,
                query=query,
                error=str(e)
            )
            raise
    
    def create_concept(
        self,
        graph_name: str,
        concept_id: str,
        concept_type: str,
        properties: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a semantic concept node
        
        Args:
            graph_name: Name of the graph
            concept_id: Unique identifier for the concept
            concept_type: Type of concept (Entity, Class, Task, etc.)
            properties: Node properties
            
        Returns:
            Created concept data
        """
        query = f"""
        CREATE (c:Concept:{concept_type} {{
            id: $id,
            type: $type,
            properties: $properties,
            created_at: timestamp()
        }})
        RETURN c
        """
        
        params = {
            "id": concept_id,
            "type": concept_type,
            "properties": properties
        }
        
        result = self.execute_query(graph_name, query, params)
        return result[0] if result else {}
    
    def update_concept(
        self,
        graph_name: str,
        concept_id: str,
        properties: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update concept properties"""
        query = """
        MATCH (c:Concept {id: $id})
        SET c.properties = $properties,
            c.updated_at = timestamp()
        RETURN c
        """
        
        params = {
            "id": concept_id,
            "properties": properties
        }
        
        result = self.execute_query(graph_name, query, params)
        return result[0] if result else {}
    
    def create_relationship(
        self,
        graph_name: str,
        source_id: str,
        target_id: str,
        relationship_type: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a relationship between concepts
        
        Args:
            graph_name: Name of the graph
            source_id: Source concept ID
            target_id: Target concept ID
            relationship_type: Type of relationship
            properties: Relationship properties
            
        Returns:
            Created relationship data
        """
        query = f"""
        MATCH (source:Concept {{id: $source_id}})
        MATCH (target:Concept {{id: $target_id}})
        CREATE (source)-[r:{relationship_type} $properties]->(target)
        RETURN r
        """
        
        params = {
            "source_id": source_id,
            "target_id": target_id,
            "properties": properties or {}
        }
        
        result = self.execute_query(graph_name, query, params)
        return result[0] if result else {}
    
    def get_lineage(
        self,
        graph_name: str,
        concept_id: str,
        direction: str = "both",
        depth: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Get lineage (upstream and downstream) for a concept
        
        Args:
            graph_name: Name of the graph
            concept_id: Concept to trace
            direction: 'upstream', 'downstream', or 'both'
            depth: Maximum depth to traverse
            
        Returns:
            List of related concepts
        """
        if direction == "upstream":
            query = f"""
            MATCH path = (c:Concept {{id: $id}})<-[*1..{depth}]-(related:Concept)
            RETURN DISTINCT related, length(path) as depth
            ORDER BY depth
            """
        elif direction == "downstream":
            query = f"""
            MATCH path = (c:Concept {{id: $id}})-[*1..{depth}]->(related:Concept)
            RETURN DISTINCT related, length(path) as depth
            ORDER BY depth
            """
        else:  # both
            query = f"""
            MATCH path = (c:Concept {{id: $id}})-[*1..{depth}]-(related:Concept)
            RETURN DISTINCT related, length(path) as depth
            ORDER BY depth
            """
        
        params = {"id": concept_id}
        return self.execute_query(graph_name, query, params)
    
    def get_impact_analysis(
        self,
        graph_name: str,
        concept_id: str
    ) -> Dict[str, Any]:
        """
        Analyze impact of changes to a concept
        
        Returns counts of affected downstream concepts by type
        """
        query = """
        MATCH (c:Concept {id: $id})-[*1..5]->(affected:Concept)
        RETURN affected.type as concept_type, count(DISTINCT affected) as count
        """
        
        params = {"id": concept_id}
        results = self.execute_query(graph_name, query, params)
        
        impact = {
            "total_affected": 0,
            "by_type": {}
        }
        
        for record in results:
            concept_type = record.get("concept_type", "Unknown")
            count = record.get("count", 0)
            impact["by_type"][concept_type] = count
            impact["total_affected"] += count
        
        return impact
    
    def delete_concept(
        self,
        graph_name: str,
        concept_id: str
    ) -> bool:
        """Delete a concept and its relationships"""
        query = """
        MATCH (c:Concept {id: $id})
        DETACH DELETE c
        """
        
        params = {"id": concept_id}
        
        try:
            self.execute_query(graph_name, query, params)
            return True
        except Exception as e:
            logger.error("Failed to delete concept", concept_id=concept_id, error=str(e))
            return False
    
    def delete_graph(self, graph_name: str) -> bool:
        """Delete an entire graph"""
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
            logger.info("FalkorDB connections closed")


# Global graph client instance
_graph_client: Optional[GraphClient] = None


def get_graph_client() -> GraphClient:
    """Get or create global graph client instance"""
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