# backend/app/schemas/diagram.py
"""
Diagram Pydantic Schemas
Path: backend/app/schemas/diagram.py
"""

from datetime import datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field
from uuid import UUID


class NodePosition(BaseModel):
    """Node position"""
    x: float
    y: float


class NodeDataBase(BaseModel):
    """Base node data"""
    label: str
    type: str
    stereotype: Optional[str] = None
    color: str
    parentId: Optional[str] = None


class AttributeBase(BaseModel):
    """Attribute schema"""
    id: str
    name: str
    dataType: str
    key: Optional[str] = 'Default'
    visibility: Optional[str] = None
    isStatic: Optional[bool] = None
    isFinal: Optional[bool] = None


class MethodBase(BaseModel):
    """Method schema"""
    id: str
    name: str
    returnType: str
    parameters: List[Dict[str, str]] = []
    visibility: Optional[str] = None
    isStatic: Optional[bool] = None
    isAbstract: Optional[bool] = None


class NodeBase(BaseModel):
    """Node schema"""
    id: str
    type: str
    position: NodePosition
    data: Dict[str, Any]


class EdgeDataBase(BaseModel):
    """Edge data schema"""
    type: str
    sourceCardinality: str
    targetCardinality: str
    label: Optional[str] = None
    color: Optional[str] = None


class EdgeBase(BaseModel):
    """Edge schema"""
    id: str
    source: str
    target: str
    data: EdgeDataBase


class ViewportBase(BaseModel):
    """Viewport schema"""
    x: float = 0
    y: float = 0
    zoom: float = 1


class DiagramCreate(BaseModel):
    """Create diagram request"""
    workspace_name: str = Field(..., min_length=1, max_length=255)
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    nodes: List[NodeBase] = []
    edges: List[EdgeBase] = []
    viewport: ViewportBase = ViewportBase()


class DiagramUpdate(BaseModel):
    """Update diagram request"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    nodes: Optional[List[NodeBase]] = None
    edges: Optional[List[EdgeBase]] = None
    viewport: Optional[ViewportBase] = None
    settings: Optional[Dict[str, Any]] = None


class DiagramResponse(BaseModel):
    """Diagram response"""
    id: UUID
    name: str
    workspace_name: Optional[str]
    description: Optional[str]
    notation: str
    graph_name: Optional[str]
    is_published: bool
    published_at: Optional[datetime]
    nodes: List[NodeBase] = []
    edges: List[EdgeBase] = []
    viewport: ViewportBase = ViewportBase()
    settings: Dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime
    created_by: UUID
    
    class Config:
        from_attributes = True


class DiagramPublicResponse(BaseModel):
    """Public response for homepage - includes computed stats"""
    id: UUID
    name: str
    workspace_name: str
    author_name: str
    total_classes: int
    total_relationships: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class DiagramListResponse(BaseModel):
    """List of diagrams"""
    diagrams: List[DiagramResponse]
    total: int