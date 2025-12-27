"""
ER Diagram Validation Rules
"""
from typing import List, Dict, Any
from app.validation.rules.base_rule import BaseRule


class ERRules(BaseRule):
    """Validation rules for ER diagrams"""
    
    def validate(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Validate ER diagram"""
        errors = []
        warnings = []
        
        # Validate entities
        entity_nodes = [n for n in nodes if n.get("type", "").startswith("ER_ENTITY")]
        
        for node in entity_nodes:
            entity_data = node.get("data", {}).get("entity")
            if not entity_data:
                errors.append({
                    "id": f"missing_entity_data_{node.get('id')}",
                    "nodeId": node.get("id"),
                    "message": "Entity node is missing entity data",
                    "severity": "error"
                })
                continue
            
            # Check for entity name
            if not entity_data.get("name"):
                errors.append({
                    "id": f"missing_entity_name_{node.get('id')}",
                    "nodeId": node.get("id"),
                    "message": "Entity must have a name",
                    "severity": "error"
                })
            
            # Check for attributes
            attributes = entity_data.get("attributes", [])
            if not attributes:
                warnings.append({
                    "id": f"no_attributes_{node.get('id')}",
                    "nodeId": node.get("id"),
                    "message": f"Entity '{entity_data.get('name', 'Unnamed')}' has no attributes",
                    "severity": "warning"
                })
            
            # Check for primary key
            has_primary_key = any(attr.get("isPrimary", False) for attr in attributes)
            if not has_primary_key and attributes:
                warnings.append({
                    "id": f"no_primary_key_{node.get('id')}",
                    "nodeId": node.get("id"),
                    "message": f"Entity '{entity_data.get('name', 'Unnamed')}' has no primary key defined",
                    "severity": "warning"
                })
            
            # Check for duplicate attribute names
            attr_names = [attr.get("name", "") for attr in attributes]
            if len(attr_names) != len(set(attr_names)):
                errors.append({
                    "id": f"duplicate_attributes_{node.get('id')}",
                    "nodeId": node.get("id"),
                    "message": f"Entity '{entity_data.get('name', 'Unnamed')}' has duplicate attribute names",
                    "severity": "error"
                })
            
            # Check attribute data types
            for attr in attributes:
                if not attr.get("type"):
                    warnings.append({
                        "id": f"missing_attribute_type_{node.get('id')}_{attr.get('id')}",
                        "nodeId": node.get("id"),
                        "message": f"Attribute '{attr.get('name', 'Unnamed')}' has no data type",
                        "severity": "warning"
                    })
        
        # Validate relationships
        relationship_edges = [e for e in edges if e.get("type") == "ER_RELATIONSHIP"]
        
        for edge in relationship_edges:
            # Check that relationships connect entities
            source_node = next((n for n in nodes if n.get("id") == edge.get("source")), None)
            target_node = next((n for n in nodes if n.get("id") == edge.get("target")), None)
            
            if source_node and not source_node.get("type", "").startswith("ER_ENTITY"):
                errors.append({
                    "id": f"invalid_relationship_source_{edge.get('id')}",
                    "edgeId": edge.get("id"),
                    "message": "Relationship must connect entities",
                    "severity": "error"
                })
            
            if target_node and not target_node.get("type", "").startswith("ER_ENTITY"):
                errors.append({
                    "id": f"invalid_relationship_target_{edge.get('id')}",
                    "edgeId": edge.get("id"),
                    "message": "Relationship must connect entities",
                    "severity": "error"
                })
        
        return {"errors": errors, "warnings": warnings}