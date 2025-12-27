"""
Validation Engine - Validates diagrams based on notation rules
"""
from typing import List, Dict, Any
from app.validation.rules.bpmn_rules import BPMNRules
from app.validation.rules.uml_rules import UMLRules
from app.validation.rules.er_rules import ERRules


class ValidationEngine:
    """Validates diagrams according to notation-specific rules"""
    
    def __init__(self):
        self.bpmn_rules = BPMNRules()
        self.uml_rules = UMLRules()
        self.er_rules = ERRules()
    
    def validate(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
        diagram_type: str
    ) -> Dict[str, Any]:
        """
        Validate diagram based on its type
        
        Args:
            nodes: List of diagram nodes
            edges: List of diagram edges
            diagram_type: Type of diagram (ER, UML_CLASS, BPMN, etc.)
            
        Returns:
            Dictionary containing validation results:
            {
                "is_valid": bool,
                "errors": List[Dict],
                "warnings": List[Dict]
            }
        """
        errors = []
        warnings = []
        
        # Select appropriate validator based on diagram type
        if diagram_type == "ER":
            results = self.er_rules.validate(nodes, edges)
        elif diagram_type.startswith("UML"):
            results = self.uml_rules.validate(nodes, edges, diagram_type)
        elif diagram_type == "BPMN":
            results = self.bpmn_rules.validate(nodes, edges)
        else:
            # Generic validation
            results = self._validate_generic(nodes, edges)
        
        errors.extend(results.get("errors", []))
        warnings.extend(results.get("warnings", []))
        
        # Common validation rules for all diagram types
        common_results = self._validate_common(nodes, edges)
        errors.extend(common_results.get("errors", []))
        warnings.extend(common_results.get("warnings", []))
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def _validate_common(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Common validation rules for all diagram types"""
        errors = []
        warnings = []
        
        # Check for duplicate node IDs
        node_ids = [n.get("id") for n in nodes]
        if len(node_ids) != len(set(node_ids)):
            errors.append({
                "id": "duplicate_node_ids",
                "message": "Diagram contains duplicate node IDs",
                "severity": "error"
            })
        
        # Check for orphaned edges
        for edge in edges:
            source = edge.get("source")
            target = edge.get("target")
            
            if source not in node_ids:
                errors.append({
                    "id": f"orphaned_edge_{edge.get('id')}",
                    "edgeId": edge.get("id"),
                    "message": f"Edge references non-existent source node: {source}",
                    "severity": "error"
                })
            
            if target not in node_ids:
                errors.append({
                    "id": f"orphaned_edge_{edge.get('id')}",
                    "edgeId": edge.get("id"),
                    "message": f"Edge references non-existent target node: {target}",
                    "severity": "error"
                })
        
        # Check for self-loops (optional warning)
        for edge in edges:
            if edge.get("source") == edge.get("target"):
                warnings.append({
                    "id": f"self_loop_{edge.get('id')}",
                    "edgeId": edge.get("id"),
                    "message": "Edge creates a self-loop",
                    "severity": "warning"
                })
        
        # Warn about isolated nodes
        connected_nodes = set()
        for edge in edges:
            connected_nodes.add(edge.get("source"))
            connected_nodes.add(edge.get("target"))
        
        for node in nodes:
            if node.get("id") not in connected_nodes:
                warnings.append({
                    "id": f"isolated_node_{node.get('id')}",
                    "nodeId": node.get("id"),
                    "message": f"Node '{node.get('data', {}).get('label', 'Unnamed')}' is not connected to any other nodes",
                    "severity": "warning"
                })
        
        return {"errors": errors, "warnings": warnings}
    
    def _validate_generic(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generic validation for unknown diagram types"""
        errors = []
        warnings = []
        
        # Just check basic structure
        if not nodes:
            warnings.append({
                "id": "empty_diagram",
                "message": "Diagram contains no nodes",
                "severity": "warning"
            })
        
        return {"errors": errors, "warnings": warnings}