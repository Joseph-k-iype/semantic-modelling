"""
Cypher Exporter - Converts diagrams to Cypher (graph query language)
"""
from typing import List, Dict, Any
from app.exporters.base_exporter import BaseExporter


class CypherExporter(BaseExporter):
    """Export diagrams to Cypher statements for graph databases"""
    
    def export(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
        diagram_type: str
    ) -> str:
        """
        Convert diagram nodes and edges to Cypher statements
        
        Args:
            nodes: List of diagram nodes
            edges: List of diagram edges
            diagram_type: Type of diagram (ER, UML_CLASS, BPMN, etc.)
            
        Returns:
            Cypher statements as a string
        """
        cypher_statements = []
        
        # Add header comment
        cypher_statements.append("// Generated Cypher statements from diagram")
        cypher_statements.append("// Generated at: " + self._get_timestamp())
        cypher_statements.append("// Diagram type: " + diagram_type)
        cypher_statements.append("")
        
        # Create nodes
        cypher_statements.append("// Create nodes")
        for node in nodes:
            node_cypher = self._generate_create_node(node, diagram_type)
            if node_cypher:
                cypher_statements.append(node_cypher)
        
        cypher_statements.append("")
        
        # Create relationships
        cypher_statements.append("// Create relationships")
        for edge in edges:
            edge_cypher = self._generate_create_relationship(edge, nodes, diagram_type)
            if edge_cypher:
                cypher_statements.append(edge_cypher)
        
        return "\n".join(cypher_statements)
    
    def _generate_create_node(self, node: Dict[str, Any], diagram_type: str) -> str:
        """Generate CREATE statement for a node"""
        node_id = self._sanitize_identifier(node.get("id", ""))
        node_type = node.get("type", "")
        node_data = node.get("data", {})
        
        # Determine label based on diagram type and node type
        if diagram_type == "ER":
            return self._generate_er_node(node_id, node_data)
        elif diagram_type.startswith("UML"):
            return self._generate_uml_node(node_id, node_type, node_data)
        elif diagram_type == "BPMN":
            return self._generate_bpmn_node(node_id, node_type, node_data)
        else:
            return self._generate_generic_node(node_id, node_type, node_data)
    
    def _generate_er_node(self, node_id: str, data: Dict[str, Any]) -> str:
        """Generate Cypher for ER entity node"""
        entity = data.get("entity")
        if not entity:
            return ""
        
        entity_name = self._sanitize_identifier(entity.get("name", "Entity"))
        attributes = entity.get("attributes", [])
        
        # Build properties
        properties = {
            "name": entity_name,
            "id": node_id,
        }
        
        # Add attributes as properties
        for attr in attributes:
            attr_name = self._sanitize_identifier(attr.get("name", ""))
            if attr_name:
                properties[f"attr_{attr_name}"] = {
                    "type": attr.get("type", "String"),
                    "nullable": attr.get("isNullable", True),
                    "unique": attr.get("isUnique", False),
                    "primary": attr.get("isPrimary", False),
                }
        
        props_str = self._format_properties(properties)
        
        return f"CREATE (:{entity_name} {props_str})"
    
    def _generate_uml_node(
        self,
        node_id: str,
        node_type: str,
        data: Dict[str, Any]
    ) -> str:
        """Generate Cypher for UML class node"""
        uml_class = data.get("class")
        if not uml_class:
            return ""
        
        class_name = self._sanitize_identifier(uml_class.get("name", "Class"))
        
        # Build properties
        properties = {
            "name": class_name,
            "id": node_id,
            "isAbstract": data.get("isAbstract", False),
        }
        
        if data.get("stereotype"):
            properties["stereotype"] = data["stereotype"]
        
        # Add attributes
        attributes = uml_class.get("attributes", [])
        if attributes:
            properties["attributes"] = [
                {
                    "name": attr.get("name"),
                    "type": attr.get("type"),
                    "visibility": attr.get("visibility"),
                }
                for attr in attributes
            ]
        
        # Add methods
        methods = uml_class.get("methods", [])
        if methods:
            properties["methods"] = [
                {
                    "name": method.get("name"),
                    "returnType": method.get("returnType"),
                    "visibility": method.get("visibility"),
                }
                for method in methods
            ]
        
        props_str = self._format_properties(properties)
        
        return f"CREATE (:{class_name}:Class {props_str})"
    
    def _generate_bpmn_node(
        self,
        node_id: str,
        node_type: str,
        data: Dict[str, Any]
    ) -> str:
        """Generate Cypher for BPMN node"""
        # Handle different BPMN element types
        if "TASK" in node_type:
            task = data.get("task")
            if not task:
                return ""
            
            task_name = self._sanitize_identifier(task.get("name", "Task"))
            
            properties = {
                "name": task_name,
                "id": node_id,
                "type": task.get("type", "task"),
            }
            
            if task.get("assignee"):
                properties["assignee"] = task["assignee"]
            
            props_str = self._format_properties(properties)
            return f"CREATE (:{task_name}:Task {props_str})"
        
        elif "EVENT" in node_type:
            event = data.get("event")
            if not event:
                return ""
            
            event_name = self._sanitize_identifier(event.get("name", "Event") or "Event")
            
            properties = {
                "id": node_id,
                "eventType": event.get("eventType", "start"),
            }
            
            if event.get("name"):
                properties["name"] = event_name
            
            props_str = self._format_properties(properties)
            return f"CREATE (:Event {props_str})"
        
        elif "GATEWAY" in node_type:
            gateway = data.get("gateway")
            if not gateway:
                return ""
            
            properties = {
                "id": node_id,
                "gatewayType": gateway.get("gatewayType", "exclusive"),
            }
            
            if gateway.get("name"):
                properties["name"] = gateway["name"]
            
            props_str = self._format_properties(properties)
            return f"CREATE (:Gateway {props_str})"
        
        return ""
    
    def _generate_generic_node(
        self,
        node_id: str,
        node_type: str,
        data: Dict[str, Any]
    ) -> str:
        """Generate generic Cypher node"""
        label = self._sanitize_identifier(node_type or "Node")
        
        properties = {
            "id": node_id,
            "label": data.get("label", ""),
        }
        
        props_str = self._format_properties(properties)
        
        return f"CREATE (:{label} {props_str})"
    
    def _generate_create_relationship(
        self,
        edge: Dict[str, Any],
        nodes: List[Dict[str, Any]],
        diagram_type: str
    ) -> str:
        """Generate CREATE statement for a relationship"""
        source_id = edge.get("source")
        target_id = edge.get("target")
        edge_type = edge.get("type", "RELATES_TO")
        edge_data = edge.get("data", {})
        
        # Find source and target nodes
        source_node = next((n for n in nodes if n.get("id") == source_id), None)
        target_node = next((n for n in nodes if n.get("id") == target_id), None)
        
        if not source_node or not target_node:
            return ""
        
        # Get node identifiers
        source_label = self._get_node_label(source_node, diagram_type)
        target_label = self._get_node_label(target_node, diagram_type)
        
        # Determine relationship type
        rel_type = self._get_relationship_type(edge_type, diagram_type)
        
        # Build relationship properties
        properties = {}
        if edge_data.get("label"):
            properties["label"] = edge_data["label"]
        
        if edge_data.get("cardinality"):
            properties["cardinality"] = edge_data["cardinality"]
        
        props_str = ""
        if properties:
            props_str = " " + self._format_properties(properties)
        
        return (
            f"MATCH (source:{source_label} {{id: '{source_id}'}}), "
            f"(target:{target_label} {{id: '{target_id}'}}) "
            f"CREATE (source)-[:{rel_type}{props_str}]->(target)"
        )
    
    def _get_node_label(self, node: Dict[str, Any], diagram_type: str) -> str:
        """Get the label for a node in Cypher"""
        node_data = node.get("data", {})
        
        if diagram_type == "ER":
            entity = node_data.get("entity")
            if entity:
                return self._sanitize_identifier(entity.get("name", "Entity"))
        
        elif diagram_type.startswith("UML"):
            uml_class = node_data.get("class")
            if uml_class:
                return self._sanitize_identifier(uml_class.get("name", "Class"))
        
        elif diagram_type == "BPMN":
            task = node_data.get("task")
            if task:
                return self._sanitize_identifier(task.get("name", "Task"))
        
        return "Node"
    
    def _get_relationship_type(self, edge_type: str, diagram_type: str) -> str:
        """Get the relationship type based on edge type"""
        # Map edge types to relationship types
        type_mapping = {
            "ER_RELATIONSHIP": "RELATES_TO",
            "UML_ASSOCIATION": "ASSOCIATED_WITH",
            "UML_AGGREGATION": "AGGREGATES",
            "UML_COMPOSITION": "COMPOSED_OF",
            "UML_GENERALIZATION": "EXTENDS",
            "UML_DEPENDENCY": "DEPENDS_ON",
            "UML_REALIZATION": "IMPLEMENTS",
            "BPMN_SEQUENCE_FLOW": "FLOWS_TO",
            "BPMN_MESSAGE_FLOW": "SENDS_MESSAGE_TO",
        }
        
        return type_mapping.get(edge_type, "RELATES_TO")
    
    def _format_properties(self, properties: Dict[str, Any]) -> str:
        """Format properties dictionary as Cypher property string"""
        import json
        
        # Convert properties to Cypher format
        prop_strings = []
        for key, value in properties.items():
            if isinstance(value, str):
                prop_strings.append(f"{key}: '{value}'")
            elif isinstance(value, bool):
                prop_strings.append(f"{key}: {str(value).lower()}")
            elif isinstance(value, (int, float)):
                prop_strings.append(f"{key}: {value}")
            elif isinstance(value, (dict, list)):
                # Use JSON for complex types
                json_value = json.dumps(value).replace('"', '\\"')
                prop_strings.append(f"{key}: '{json_value}'")
        
        return "{" + ", ".join(prop_strings) + "}"
    
    def _sanitize_identifier(self, identifier: str) -> str:
        """Sanitize identifier for Cypher"""
        # Remove special characters and replace spaces with underscores
        sanitized = "".join(c if c.isalnum() or c == "_" else "_" for c in identifier)
        
        # Ensure doesn't start with a number
        if sanitized and sanitized[0].isdigit():
            sanitized = "_" + sanitized
        
        return sanitized or "Node"
    
    def _get_timestamp(self) -> str:
        """Get current timestamp as string"""
        from datetime import datetime
        return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")