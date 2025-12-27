"""
Layered Layout - Hierarchical layout with layers
"""
from typing import Dict, Any, List
import math


class LayeredLayout:
    """Layered (hierarchical) layout algorithm"""
    
    def compute(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
        constraints: Dict[str, Any],
        settings: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compute layered layout
        
        Args:
            nodes: List of nodes
            edges: List of edges
            constraints: Layout constraints
            settings: Algorithm settings
            
        Returns:
            Nodes with computed positions
        """
        direction = settings.get("direction", "TB")  # TB, BT, LR, RL
        layer_spacing = settings.get("layer_spacing", 100)
        node_spacing = settings.get("node_spacing", 80)
        
        # Build adjacency list
        adj_list = self._build_adjacency_list(nodes, edges)
        
        # Assign layers using topological sort
        layers = self._assign_layers(nodes, adj_list)
        
        # Position nodes within layers
        positioned_nodes = self._position_nodes(
            nodes, layers, direction, layer_spacing, node_spacing
        )
        
        return {
            "nodes": positioned_nodes,
            "edges": edges,
            "algorithm": "layered",
            "applied": True,
            "layers": len(layers)
        }
    
    def _build_adjacency_list(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]]
    ) -> Dict[str, List[str]]:
        """Build adjacency list from edges"""
        adj = {node["id"]: [] for node in nodes}
        for edge in edges:
            source = edge.get("source")
            target = edge.get("target")
            if source and target:
                adj[source].append(target)
        return adj
    
    def _assign_layers(
        self,
        nodes: List[Dict[str, Any]],
        adj_list: Dict[str, List[str]]
    ) -> List[List[str]]:
        """Assign nodes to layers"""
        # Simple layering - nodes with no incoming edges in layer 0
        # Then iteratively assign remaining nodes
        layers = []
        node_to_layer = {}
        unassigned = set(node["id"] for node in nodes)
        
        current_layer = 0
        while unassigned:
            # Find nodes with all dependencies satisfied
            layer_nodes = []
            for node_id in list(unassigned):
                # Check if all dependencies are assigned
                dependencies_satisfied = True
                for other_id in adj_list:
                    if node_id in adj_list[other_id]:
                        if other_id in unassigned:
                            dependencies_satisfied = False
                            break
                
                if dependencies_satisfied:
                    layer_nodes.append(node_id)
            
            if not layer_nodes:
                # No progress - break cycles by taking any remaining
                layer_nodes = [list(unassigned)[0]]
            
            layers.append(layer_nodes)
            for node_id in layer_nodes:
                node_to_layer[node_id] = current_layer
                unassigned.remove(node_id)
            
            current_layer += 1
        
        return layers
    
    def _position_nodes(
        self,
        nodes: List[Dict[str, Any]],
        layers: List[List[str]],
        direction: str,
        layer_spacing: int,
        node_spacing: int
    ) -> List[Dict[str, Any]]:
        """Position nodes based on layers"""
        positioned = []
        node_map = {node["id"]: node for node in nodes}
        
        for layer_idx, layer_nodes in enumerate(layers):
            layer_size = len(layer_nodes)
            
            for node_idx, node_id in enumerate(layer_nodes):
                node = node_map[node_id].copy()
                
                if direction in ["TB", "BT"]:  # Top-to-bottom or bottom-to-top
                    x = (node_idx - layer_size / 2) * node_spacing
                    y = layer_idx * layer_spacing
                    if direction == "BT":
                        y = -y
                else:  # Left-to-right or right-to-left
                    x = layer_idx * layer_spacing
                    y = (node_idx - layer_size / 2) * node_spacing
                    if direction == "RL":
                        x = -x
                
                node["position"] = {"x": x, "y": y}
                positioned.append(node)
        
        return positioned