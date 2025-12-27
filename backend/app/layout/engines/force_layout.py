"""
Force-Directed Layout - Physics-based layout
"""
from typing import Dict, Any, List
import math
import random


class ForceLayout:
    """Force-directed layout algorithm"""
    
    def compute(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
        constraints: Dict[str, Any],
        settings: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compute force-directed layout
        
        Args:
            nodes: List of nodes
            edges: List of edges
            constraints: Layout constraints (pinned nodes, etc.)
            settings: Algorithm settings
            
        Returns:
            Nodes with computed positions
        """
        iterations = settings.get("iterations", 100)
        repulsion = settings.get("repulsion", 100)
        attraction = settings.get("attraction", 0.1)
        damping = settings.get("damping", 0.85)
        
        # Initialize positions if not present
        positioned_nodes = self._initialize_positions(nodes)
        
        # Get pinned nodes from constraints
        pinned = constraints.get("pinned_nodes", [])
        
        # Run force simulation
        for _ in range(iterations):
            positioned_nodes = self._apply_forces(
                positioned_nodes, edges, repulsion, attraction, damping, pinned
            )
        
        return {
            "nodes": positioned_nodes,
            "edges": edges,
            "algorithm": "force_directed",
            "applied": True,
            "iterations": iterations
        }
    
    def _initialize_positions(self, nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Initialize node positions randomly if not present"""
        initialized = []
        for node in nodes:
            node_copy = node.copy()
            if "position" not in node_copy or not node_copy["position"]:
                node_copy["position"] = {
                    "x": random.uniform(-200, 200),
                    "y": random.uniform(-200, 200)
                }
            # Initialize velocity
            node_copy["velocity"] = {"x": 0, "y": 0}
            initialized.append(node_copy)
        return initialized
    
    def _apply_forces(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
        repulsion: float,
        attraction: float,
        damping: float,
        pinned: List[str]
    ) -> List[Dict[str, Any]]:
        """Apply forces to nodes"""
        node_map = {node["id"]: node for node in nodes}
        
        # Reset forces
        for node in nodes:
            node["force"] = {"x": 0, "y": 0}
        
        # Repulsive forces between all nodes
        for i, node1 in enumerate(nodes):
            for node2 in nodes[i+1:]:
                self._apply_repulsion(node1, node2, repulsion)
        
        # Attractive forces along edges
        for edge in edges:
            source = node_map.get(edge.get("source"))
            target = node_map.get(edge.get("target"))
            if source and target:
                self._apply_attraction(source, target, attraction)
        
        # Update positions
        updated_nodes = []
        for node in nodes:
            if node["id"] in pinned:
                # Skip pinned nodes
                updated_nodes.append(node)
                continue
            
            # Update velocity and position
            node["velocity"]["x"] = (node["velocity"]["x"] + node["force"]["x"]) * damping
            node["velocity"]["y"] = (node["velocity"]["y"] + node["force"]["y"]) * damping
            
            node["position"]["x"] += node["velocity"]["x"]
            node["position"]["y"] += node["velocity"]["y"]
            
            updated_nodes.append(node)
        
        return updated_nodes
    
    def _apply_repulsion(self, node1: Dict, node2: Dict, strength: float):
        """Apply repulsive force between two nodes"""
        dx = node2["position"]["x"] - node1["position"]["x"]
        dy = node2["position"]["y"] - node1["position"]["y"]
        distance = math.sqrt(dx * dx + dy * dy) or 1
        
        force = strength / (distance * distance)
        fx = (dx / distance) * force
        fy = (dy / distance) * force
        
        node1["force"]["x"] -= fx
        node1["force"]["y"] -= fy
        node2["force"]["x"] += fx
        node2["force"]["y"] += fy
    
    def _apply_attraction(self, source: Dict, target: Dict, strength: float):
        """Apply attractive force along an edge"""
        dx = target["position"]["x"] - source["position"]["x"]
        dy = target["position"]["y"] - source["position"]["y"]
        
        fx = dx * strength
        fy = dy * strength
        
        source["force"]["x"] += fx
        source["force"]["y"] += fy
        target["force"]["x"] -= fx
        target["force"]["y"] -= fy