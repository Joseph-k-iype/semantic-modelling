"""
Diagram Schemas - Pydantic models for diagram API
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class DiagramNodeBase(BaseModel):
    """Base schema for diagram nodes"""
    id: str
    type: str
    position: Dict[str, float]
    data: Dict[str, Any]


class DiagramEdgeBase(BaseModel):
    """Base schema for diagram edges"""
    id: str
    source: str
    target: str
    type: str
    data: Optional[Dict[str, Any]] = None


class DiagramBase(BaseModel):
    """Base schema for diagrams"""
    name: str
    type: str
    model_id: str
    workspace_id: str


class DiagramCreate(DiagramBase):
    """Schema for creating a diagram"""
    nodes: Optional[List[Dict[str, Any]]] = []
    edges: Optional[List[Dict[str, Any]]] = []
    viewport: Optional[Dict[str, Any]] = None


class DiagramUpdate(BaseModel):
    """Schema for updating a diagram"""
    name: Optional[str] = None
    type: Optional[str] = None
    nodes: Optional[List[Dict[str, Any]]] = None
    edges: Optional[List[Dict[str, Any]]] = None
    viewport: Optional[Dict[str, Any]] = None


class DiagramResponse(DiagramBase):
    """Schema for diagram response"""
    id: str
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: str
    
    class Config:
        from_attributes = True


class DiagramDetailResponse(DiagramResponse):
    """Schema for detailed diagram response"""
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    viewport: Dict[str, Any]
    
    class Config:
        from_attributes = True