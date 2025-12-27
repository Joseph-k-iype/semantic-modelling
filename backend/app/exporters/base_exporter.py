"""
Base Exporter - Abstract base class for diagram exporters
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseExporter(ABC):
    """Abstract base class for diagram exporters"""
    
    @abstractmethod
    def export(self, nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]], **kwargs) -> str:
        """
        Export diagram to target format
        
        Args:
            nodes: List of diagram nodes
            edges: List of diagram edges
            **kwargs: Additional export options
            
        Returns:
            Exported content as string
        """
        pass