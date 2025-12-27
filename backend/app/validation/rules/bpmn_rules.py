"""
BPMN Diagram Validation Rules
"""
from typing import List, Dict, Any
from app.validation.rules.base_rule import BaseRule


class BPMNRules(BaseRule):
    """Validation rules for BPMN diagrams"""
    
    def validate(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Validate BPMN diagram"""
        errors = []
        warnings = []
        
        # Check for start and end events
        start_events = [n for n in nodes if n.get("type") == "BPMN_START_EVENT"]
        end_events = [n for n in nodes if n.get("type") == "BPMN_END_EVENT"]
        
        if not start_events:
            warnings.append({
                "id": "no_start_event",
                "message": "BPMN diagram should have at least one start event",
                "severity": "warning"
            })
        
        if not end_events:
            warnings.append({
                "id": "no_end_event",
                "message": "BPMN diagram should have at least one end event",
                "severity": "warning"
            })
        
        # Validate gateways
        gateway_nodes = [
            n for n in nodes 
            if n.get("type", "").startswith("BPMN_GATEWAY")
        ]
        
        for gateway in gateway_nodes:
            # Check incoming and outgoing edges
            node_id = gateway.get("id")
            incoming_edges = [e for e in edges if e.get("target") == node_id]
            outgoing_edges = [e for e in edges if e.get("source") == node_id]
            
            gateway_data = gateway.get("data", {}).get("gateway")
            gateway_type = gateway_data.get("gatewayType") if gateway_data else None
            
            # Parallel gateways should have multiple incoming or outgoing
            if gateway_type == "parallel":
                if len(incoming_edges) < 2 and len(outgoing_edges) < 2:
                    warnings.append({
                        "id": f"invalid_parallel_gateway_{node_id}",
                        "nodeId": node_id,
                        "message": "Parallel gateway should have multiple incoming or outgoing flows",
                        "severity": "warning"
                    })
            
            # Exclusive gateways should have at least 2 outgoing when used as split
            if gateway_type == "exclusive" and len(incoming_edges) == 1:
                if len(outgoing_edges) < 2:
                    warnings.append({
                        "id": f"invalid_exclusive_gateway_{node_id}",
                        "nodeId": node_id,
                        "message": "Exclusive gateway (split) should have at least 2 outgoing flows",
                        "severity": "warning"
                    })
        
        # Validate sequence flows
        sequence_flows = [e for e in edges if e.get("type") == "BPMN_SEQUENCE_FLOW"]
        
        for edge in sequence_flows:
            # Sequence flows should connect valid BPMN elements
            source_node = next((n for n in nodes if n.get("id") == edge.get("source")), None)
            target_node = next((n for n in nodes if n.get("id") == edge.get("target")), None)
            
            if source_node:
                source_type = source_node.get("type", "")
                # Start events should not have incoming sequence flows
                if source_type == "BPMN_START_EVENT":
                    incoming = [e for e in sequence_flows if e.get("target") == edge.get("source")]
                    if incoming:
                        errors.append({
                            "id": f"invalid_start_event_incoming_{edge.get('id')}",
                            "nodeId": source_node.get("id"),
                            "message": "Start event cannot have incoming sequence flows",
                            "severity": "error"
                        })
            
            if target_node:
                target_type = target_node.get("type", "")
                # End events should not have outgoing sequence flows
                if target_type == "BPMN_END_EVENT":
                    outgoing = [e for e in sequence_flows if e.get("source") == edge.get("target")]
                    if outgoing:
                        errors.append({
                            "id": f"invalid_end_event_outgoing_{edge.get('id')}",
                            "nodeId": target_node.get("id"),
                            "message": "End event cannot have outgoing sequence flows",
                            "severity": "error"
                        })
        
        # Check for unreachable tasks
        reachable_nodes = self._find_reachable_nodes(start_events, edges)
        task_nodes = [n for n in nodes if "TASK" in n.get("type", "")]
        
        for task in task_nodes:
            if task.get("id") not in reachable_nodes:
                warnings.append({
                    "id": f"unreachable_task_{task.get('id')}",
                    "nodeId": task.get("id"),
                    "message": f"Task is not reachable from any start event",
                    "severity": "warning"
                })
        
        return {"errors": errors, "warnings": warnings}
    
    def _find_reachable_nodes(
        self,
        start_nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]]
    ) -> set:
        """Find all nodes reachable from start nodes"""
        reachable = set()
        to_visit = [n.get("id") for n in start_nodes]
        
        while to_visit:
            current = to_visit.pop(0)
            if current in reachable:
                continue
            
            reachable.add(current)
            
            # Find outgoing edges
            outgoing = [e.get("target") for e in edges if e.get("source") == current]
            to_visit.extend(outgoing)
        
        return reachable