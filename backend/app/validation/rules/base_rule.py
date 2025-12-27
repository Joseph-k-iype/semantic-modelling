"""
Base Rule - Abstract base class for validation rules
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseRule(ABC):
    """Abstract base class for validation rules"""
    
    @abstractmethod
    def validate(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Validate diagram nodes and edges
        
        Args:
            nodes: List of diagram nodes
            edges: List of diagram edges
            **kwargs: Additional validation options
            
        Returns:
            Dictionary containing errors and warnings:
            {
                "errors": List[Dict],
                "warnings": List[Dict]
            }
        """
        pass