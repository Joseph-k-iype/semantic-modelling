"""
Layout Engine - Main layout orchestration
"""
from typing import Dict, Any, List
from app.layout.engines.manual_layout import ManualLayout
from app.layout.engines.layered_layout import LayeredLayout
from app.layout.engines.force_layout import ForceLayout


class LayoutEngine:
    """Main layout engine that orchestrates different layout algorithms"""
    
    def __init__(self):
        self.algorithms = {
            "manual": ManualLayout(),
            "layered": LayeredLayout(),
            "force_directed": ForceLayout(),
        }
    
    def compute_layout(
        self,
        algorithm: str,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
        constraints: Dict[str, Any] = None,
        settings: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Compute layout using specified algorithm
        
        Args:
            algorithm: Layout algorithm name
            nodes: List of nodes
            edges: List of edges
            constraints: Layout constraints
            settings: Algorithm-specific settings
            
        Returns:
            Layout result with positioned nodes
        """
        if algorithm not in self.algorithms:
            raise ValueError(f"Unknown layout algorithm: {algorithm}")
        
        layout_algo = self.algorithms[algorithm]
        return layout_algo.compute(
            nodes=nodes,
            edges=edges,
            constraints=constraints or {},
            settings=settings or {}
        )