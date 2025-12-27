"""
Manual Layout - User-controlled positioning
"""
from typing import Dict, Any, List


class ManualLayout:
    """Manual layout preserves user-defined positions"""
    
    def compute(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
        constraints: Dict[str, Any],
        settings: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Manual layout just returns nodes with their current positions
        
        Args:
            nodes: List of nodes with positions
            edges: List of edges
            constraints: Ignored for manual layout
            settings: Ignored for manual layout
            
        Returns:
            Nodes with preserved positions
        """
        return {
            "nodes": nodes,
            "edges": edges,
            "algorithm": "manual",
            "applied": True
        }