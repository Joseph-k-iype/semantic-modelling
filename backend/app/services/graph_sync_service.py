# backend/app/services/graph_sync_service.py

from typing import Dict, Any, List, Optional
from app.graph.client import get_graph_client
import json
import logging

logger = logging.getLogger(__name__)


class GraphSyncService:
    """Service for synchronizing diagram elements with graph database"""
    
    def __init__(self):
        self.graph = get_graph_client()
    
    async def sync_er_entity(
        self,
        model_id: str,
        diagram_id: str,
        node_id: str,
        node_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Sync ER entity node to graph database
        
        Creates or updates Entity concept with attributes and keys
        """
        try:
            entity_name = node_data.get('label', 'Unnamed Entity')
            attributes = node_data.get('attributes', [])
            is_weak = node_data.get('isWeak', False)
            
            # Create or update entity concept in graph
            query = """
            MERGE (e:Entity {id: $entity_id, model_id: $model_id})
            SET e.name = $entity_name,
                e.is_weak = $is_weak,
                e.diagram_id = $diagram_id,
                e.node_id = $node_id,
                e.color = $color,
                e.text_color = $text_color,
                e.updated_at = datetime()
            RETURN e
            """
            
            params = {
                'entity_id': f"{model_id}:{node_id}",
                'model_id': model_id,
                'diagram_id': diagram_id,
                'node_id': node_id,
                'entity_name': entity_name,
                'is_weak': is_weak,
                'color': node_data.get('color', '#ffffff'),
                'text_color': node_data.get('textColor', '#000000')
            }
            
            result = await self.graph.execute_query(query, params)
            
            # Sync attributes
            await self._sync_entity_attributes(
                f"{model_id}:{node_id}",
                attributes
            )
            
            return {
                'success': True,
                'entity_id': f"{model_id}:{node_id}",
                'message': 'Entity synchronized successfully'
            }
            
        except Exception as e:
            logger.error(f"Error syncing ER entity: {str(e)}")
            raise
    
    async def _sync_entity_attributes(
        self,
        entity_id: str,
        attributes: List[Dict[str, Any]]
    ):
        """Sync entity attributes to graph"""
        try:
            # Delete existing attributes
            delete_query = """
            MATCH (e:Entity {id: $entity_id})-[r:HAS_ATTRIBUTE]->(a:Attribute)
            DELETE r, a
            """
            await self.graph.execute_query(delete_query, {'entity_id': entity_id})
            
            # Create new attributes
            for attr in attributes:
                attr_query = """
                MATCH (e:Entity {id: $entity_id})
                CREATE (a:Attribute {
                    id: $attr_id,
                    name: $name,
                    type: $type,
                    is_primary_key: $is_pk,
                    is_foreign_key: $is_fk,
                    nullable: $nullable
                })
                CREATE (e)-[:HAS_ATTRIBUTE]->(a)
                """
                
                attr_params = {
                    'entity_id': entity_id,
                    'attr_id': attr['id'],
                    'name': attr['name'],
                    'type': attr['type'],
                    'is_pk': attr.get('isPrimaryKey', False),
                    'is_fk': attr.get('isForeignKey', False),
                    'nullable': attr.get('nullable', True)
                }
                
                await self.graph.execute_query(attr_query, attr_params)
                
        except Exception as e:
            logger.error(f"Error syncing entity attributes: {str(e)}")
            raise
    
    async def sync_er_relationship(
        self,
        model_id: str,
        diagram_id: str,
        edge_id: str,
        edge_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Sync ER relationship edge to graph database
        """
        try:
            source_id = f"{model_id}:{edge_data['source']}"
            target_id = f"{model_id}:{edge_data['target']}"
            relationship_name = edge_data.get('data', {}).get('label', 'relates_to')
            source_cardinality = edge_data.get('data', {}).get('sourceCardinality', '1')
            target_cardinality = edge_data.get('data', {}).get('targetCardinality', 'N')
            
            # Create relationship in graph
            query = """
            MATCH (source:Entity {id: $source_id})
            MATCH (target:Entity {id: $target_id})
            MERGE (source)-[r:RELATES_TO {
                id: $relationship_id,
                diagram_id: $diagram_id,
                edge_id: $edge_id
            }]->(target)
            SET r.name = $name,
                r.source_cardinality = $source_cardinality,
                r.target_cardinality = $target_cardinality,
                r.color = $color,
                r.updated_at = datetime()
            RETURN r
            """
            
            params = {
                'source_id': source_id,
                'target_id': target_id,
                'relationship_id': f"{model_id}:{edge_id}",
                'diagram_id': diagram_id,
                'edge_id': edge_id,
                'name': relationship_name,
                'source_cardinality': source_cardinality,
                'target_cardinality': target_cardinality,
                'color': edge_data.get('data', {}).get('color', '#6b7280')
            }
            
            result = await self.graph.execute_query(query, params)
            
            return {
                'success': True,
                'relationship_id': f"{model_id}:{edge_id}",
                'message': 'Relationship synchronized successfully'
            }
            
        except Exception as e:
            logger.error(f"Error syncing ER relationship: {str(e)}")
            raise
    
    async def sync_uml_class(
        self,
        model_id: str,
        diagram_id: str,
        node_id: str,
        node_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Sync UML class to graph database"""
        try:
            class_name = node_data.get('label', 'Unnamed Class')
            class_type = node_data.get('classType', 'class')
            attributes = node_data.get('attributes', [])
            methods = node_data.get('methods', [])
            
            # Create or update class concept
            query = """
            MERGE (c:Class {id: $class_id, model_id: $model_id})
            SET c.name = $class_name,
                c.class_type = $class_type,
                c.diagram_id = $diagram_id,
                c.node_id = $node_id,
                c.color = $color,
                c.text_color = $text_color,
                c.attributes = $attributes,
                c.methods = $methods,
                c.updated_at = datetime()
            RETURN c
            """
            
            params = {
                'class_id': f"{model_id}:{node_id}",
                'model_id': model_id,
                'diagram_id': diagram_id,
                'node_id': node_id,
                'class_name': class_name,
                'class_type': class_type,
                'color': node_data.get('color', '#ffffff'),
                'text_color': node_data.get('textColor', '#000000'),
                'attributes': json.dumps(attributes),
                'methods': json.dumps(methods)
            }
            
            result = await self.graph.execute_query(query, params)
            
            return {
                'success': True,
                'class_id': f"{model_id}:{node_id}",
                'message': 'Class synchronized successfully'
            }
            
        except Exception as e:
            logger.error(f"Error syncing UML class: {str(e)}")
            raise
    
    async def sync_uml_relationship(
        self,
        model_id: str,
        diagram_id: str,
        edge_id: str,
        edge_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Sync UML class relationship to graph database"""
        try:
            source_id = f"{model_id}:{edge_data['source']}"
            target_id = f"{model_id}:{edge_data['target']}"
            relationship_type = edge_data.get('data', {}).get('relationshipType', 'association')
            
            # Determine relationship type in graph
            rel_type_map = {
                'association': 'ASSOCIATES_WITH',
                'generalization': 'EXTENDS',
                'dependency': 'DEPENDS_ON',
                'aggregation': 'AGGREGATES',
                'composition': 'COMPOSES'
            }
            
            graph_rel_type = rel_type_map.get(relationship_type, 'ASSOCIATES_WITH')
            
            query = f"""
            MATCH (source:Class {{id: $source_id}})
            MATCH (target:Class {{id: $target_id}})
            MERGE (source)-[r:{graph_rel_type} {{
                id: $relationship_id,
                diagram_id: $diagram_id,
                edge_id: $edge_id
            }}]->(target)
            SET r.updated_at = datetime()
            RETURN r
            """
            
            params = {
                'source_id': source_id,
                'target_id': target_id,
                'relationship_id': f"{model_id}:{edge_id}",
                'diagram_id': diagram_id,
                'edge_id': edge_id
            }
            
            result = await self.graph.execute_query(query, params)
            
            return {
                'success': True,
                'relationship_id': f"{model_id}:{edge_id}",
                'message': 'UML relationship synchronized successfully'
            }
            
        except Exception as e:
            logger.error(f"Error syncing UML relationship: {str(e)}")
            raise
    
    async def sync_bpmn_element(
        self,
        model_id: str,
        diagram_id: str,
        node_id: str,
        node_data: Dict[str, Any],
        element_type: str
    ) -> Dict[str, Any]:
        """Sync BPMN element to graph database"""
        try:
            element_name = node_data.get('label', f'Unnamed {element_type}')
            
            # Create label based on element type
            label_map = {
                'task': 'Task',
                'event': 'Event',
                'gateway': 'Gateway',
                'pool': 'Pool'
            }
            
            graph_label = label_map.get(element_type, 'BPMNElement')
            
            query = f"""
            MERGE (e:{graph_label} {{id: $element_id, model_id: $model_id}})
            SET e.name = $element_name,
                e.element_type = $element_type,
                e.diagram_id = $diagram_id,
                e.node_id = $node_id,
                e.properties = $properties,
                e.color = $color,
                e.text_color = $text_color,
                e.updated_at = datetime()
            RETURN e
            """
            
            params = {
                'element_id': f"{model_id}:{node_id}",
                'model_id': model_id,
                'diagram_id': diagram_id,
                'node_id': node_id,
                'element_name': element_name,
                'element_type': element_type,
                'properties': json.dumps(node_data),
                'color': node_data.get('color', '#ffffff'),
                'text_color': node_data.get('textColor', '#000000')
            }
            
            result = await self.graph.execute_query(query, params)
            
            return {
                'success': True,
                'element_id': f"{model_id}:{node_id}",
                'message': f'BPMN {element_type} synchronized successfully'
            }
            
        except Exception as e:
            logger.error(f"Error syncing BPMN element: {str(e)}")
            raise
    
    async def sync_bpmn_flow(
        self,
        model_id: str,
        diagram_id: str,
        edge_id: str,
        edge_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Sync BPMN sequence/message flow to graph database"""
        try:
            source_id = f"{model_id}:{edge_data['source']}"
            target_id = f"{model_id}:{edge_data['target']}"
            flow_type = edge_data.get('data', {}).get('flowType', 'sequence')
            
            rel_type = 'SEQUENCE_FLOW' if flow_type == 'sequence' else 'MESSAGE_FLOW'
            
            query = f"""
            MATCH (source {{id: $source_id}})
            MATCH (target {{id: $target_id}})
            MERGE (source)-[r:{rel_type} {{
                id: $flow_id,
                diagram_id: $diagram_id,
                edge_id: $edge_id
            }}]->(target)
            SET r.updated_at = datetime()
            RETURN r
            """
            
            params = {
                'source_id': source_id,
                'target_id': target_id,
                'flow_id': f"{model_id}:{edge_id}",
                'diagram_id': diagram_id,
                'edge_id': edge_id
            }
            
            result = await self.graph.execute_query(query, params)
            
            return {
                'success': True,
                'flow_id': f"{model_id}:{edge_id}",
                'message': f'BPMN {flow_type} flow synchronized successfully'
            }
            
        except Exception as e:
            logger.error(f"Error syncing BPMN flow: {str(e)}")
            raise
    
    async def get_lineage(
        self,
        element_id: str,
        depth: int = 3
    ) -> Dict[str, Any]:
        """Get lineage information for an element"""
        try:
            query = """
            MATCH path = (e {id: $element_id})-[*1..$depth]-(related)
            RETURN path
            """
            
            params = {
                'element_id': element_id,
                'depth': depth
            }
            
            result = await self.graph.execute_query(query, params)
            
            return {
                'success': True,
                'lineage': result
            }
            
        except Exception as e:
            logger.error(f"Error getting lineage: {str(e)}")
            raise
    
    async def get_impact_analysis(
        self,
        element_id: str
    ) -> Dict[str, Any]:
        """Get impact analysis for an element"""
        try:
            query = """
            MATCH (e {id: $element_id})
            OPTIONAL MATCH (e)-[r]->(downstream)
            OPTIONAL MATCH (upstream)-[r2]->(e)
            RETURN e, collect(DISTINCT downstream) as affected_elements, 
                   collect(DISTINCT upstream) as dependent_elements
            """
            
            params = {'element_id': element_id}
            
            result = await self.graph.execute_query(query, params)
            
            return {
                'success': True,
                'impact_analysis': result
            }
            
        except Exception as e:
            logger.error(f"Error getting impact analysis: {str(e)}")
            raise


# Create service instance
graph_sync_service = GraphSyncService()