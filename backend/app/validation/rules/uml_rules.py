"""
UML Diagram Validation Rules
"""
from typing import List, Dict, Any
from app.validation.rules.base_rule import BaseRule


class UMLRules(BaseRule):
    """Validation rules for UML diagrams"""
    
    def validate(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
        diagram_type: str
    ) -> Dict[str, Any]:
        """Validate UML diagram"""
        errors = []
        warnings = []
        
        # Validate based on specific UML diagram type
        if diagram_type == "UML_CLASS":
            results = self._validate_class_diagram(nodes, edges)
            errors.extend(results.get("errors", []))
            warnings.extend(results.get("warnings", []))
        
        return {"errors": errors, "warnings": warnings}
    
    def _validate_class_diagram(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Validate UML class diagram"""
        errors = []
        warnings = []
        
        # Validate classes
        class_nodes = [n for n in nodes if n.get("type", "").startswith("UML_CLASS")]
        
        for node in class_nodes:
            class_data = node.get("data", {}).get("class")
            if not class_data:
                errors.append({
                    "id": f"missing_class_data_{node.get('id')}",
                    "nodeId": node.get("id"),
                    "message": "Class node is missing class data",
                    "severity": "error"
                })
                continue
            
            # Check for class name
            if not class_data.get("name"):
                errors.append({
                    "id": f"missing_class_name_{node.get('id')}",
                    "nodeId": node.get("id"),
                    "message": "Class must have a name",
                    "severity": "error"
                })
            
            # Validate attributes
            attributes = class_data.get("attributes", [])
            attr_names = [attr.get("name", "") for attr in attributes]
            
            # Check for duplicate attribute names
            if len(attr_names) != len(set(attr_names)):
                errors.append({
                    "id": f"duplicate_attributes_{node.get('id')}",
                    "nodeId": node.get("id"),
                    "message": f"Class '{class_data.get('name', 'Unnamed')}' has duplicate attribute names",
                    "severity": "error"
                })
            
            # Validate methods
            methods = class_data.get("methods", [])
            method_signatures = []
            
            for method in methods:
                signature = f"{method.get('name', '')}({','.join([p.get('type', '') for p in method.get('parameters', [])])})"
                method_signatures.append(signature)
            
            # Check for duplicate method signatures
            if len(method_signatures) != len(set(method_signatures)):
                warnings.append({
                    "id": f"duplicate_methods_{node.get('id')}",
                    "nodeId": node.get("id"),
                    "message": f"Class '{class_data.get('name', 'Unnamed')}' has duplicate method signatures",
                    "severity": "warning"
                })
        
        # Validate relationships
        generalization_edges = [e for e in edges if e.get("type") == "UML_GENERALIZATION"]
        
        # Check for circular inheritance
        for edge in generalization_edges:
            if self._has_circular_inheritance(edge, generalization_edges, nodes):
                errors.append({
                    "id": f"circular_inheritance_{edge.get('id')}",
                    "edgeId": edge.get("id"),
                    "message": "Circular inheritance detected",
                    "severity": "error"
                })
        
        return {"errors": errors, "warnings": warnings}
    
    def _has_circular_inheritance(
        self,
        edge: Dict[str, Any],
        all_edges: List[Dict[str, Any]],
        nodes: List[Dict[str, Any]],
        visited: set = None
    ) -> bool:
        """Check for circular inheritance"""
        if visited is None:
            visited = set()
        
        source = edge.get("source")
        target = edge.get("target")
        
        if target in visited:
            return True
        
        visited.add(target)
        
        # Find edges where target is the source
        next_edges = [e for e in all_edges if e.get("source") == target]
        
        for next_edge in next_edges:
            if self._has_circular_inheritance(next_edge, all_edges, nodes, visited.copy()):
                return True
        
        return False