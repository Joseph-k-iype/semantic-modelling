# backend/app/schemas/diagram.py
"""
Diagram Pydantic Schemas - Complete with all node types
Path: backend/app/schemas/diagram.py
"""

from datetime import datetime
from typing import List, Optional, Any, Dict, Union
from pydantic import BaseModel, Field
from uuid import UUID


# ============================================================================
# NODE DATA SCHEMAS
# ============================================================================

class NodePosition(BaseModel):
    """Node position"""
    x: float
    y: float


class AttributeBase(BaseModel):
    """Attribute schema for Class/Object nodes"""
    id: str
    name: str
    dataType: str
    key: Optional[str] = 'Default'
    visibility: Optional[str] = 'public'
    isStatic: Optional[bool] = False
    isFinal: Optional[bool] = False
    defaultValue: Optional[str] = None


class MethodParameter(BaseModel):
    """Method parameter"""
    name: str
    type: str


class MethodBase(BaseModel):
    """Method schema for Class/Interface nodes"""
    id: str
    name: str
    returnType: str
    parameters: List[MethodParameter] = []
    visibility: Optional[str] = 'public'
    isStatic: Optional[bool] = False
    isAbstract: Optional[bool] = False


class NodeDataBase(BaseModel):
    """Base node data - common to all node types"""
    label: str
    type: str
    stereotype: Optional[str] = None
    color: str
    parentId: Optional[str] = None
    zIndex: Optional[int] = None


class PackageNodeData(NodeDataBase):
    """Package node data"""
    isExpanded: Optional[bool] = True
    childCount: Optional[int] = 0


class ClassNodeData(NodeDataBase):
    """Class node data"""
    attributes: List[AttributeBase] = []
    methods: Optional[List[MethodBase]] = []
    isAbstract: Optional[bool] = False


class ObjectNodeData(NodeDataBase):
    """Object node data"""
    attributes: List[AttributeBase] = []


class InterfaceNodeData(NodeDataBase):
    """Interface node data"""
    methods: Optional[List[MethodBase]] = []


class EnumerationNodeData(NodeDataBase):
    """Enumeration node data"""
    literals: List[str] = []


class NodeBase(BaseModel):
    """Node schema - represents a diagram node"""
    id: str
    type: str
    position: NodePosition
    data: Dict[str, Any]  # Can be any of the node data types above
    
    class Config:
        arbitrary_types_allowed = True


# ============================================================================
# EDGE DATA SCHEMAS
# ============================================================================

class EdgeDataBase(BaseModel):
    """Edge data schema"""
    type: str
    sourceCardinality: str
    targetCardinality: str
    label: Optional[str] = None
    color: Optional[str] = None
    strokeWidth: Optional[float] = 2.0
    isIdentifying: Optional[bool] = False


class EdgeBase(BaseModel):
    """Edge schema - represents a relationship"""
    id: str
    source: str
    target: str
    data: EdgeDataBase
    sourceHandle: Optional[str] = None
    targetHandle: Optional[str] = None


# ============================================================================
# VIEWPORT SCHEMA
# ============================================================================

class ViewportBase(BaseModel):
    """Viewport schema"""
    x: float = 0
    y: float = 0
    zoom: float = 1


# ============================================================================
# DIAGRAM REQUEST/RESPONSE SCHEMAS
# ============================================================================

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


class DiagramResponse(BaseModel):
    """Diagram response"""
    id: UUID
    name: str
    description: Optional[str]
    workspace_name: str
    graph_name: str
    notation: str
    is_published: bool
    published_at: Optional[datetime]
    settings: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]
    
    class Config:
        from_attributes = True
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat() if v else None
        }


class DiagramPublicResponse(BaseModel):
    """Public diagram response (for published diagrams)"""
    id: UUID
    name: str
    description: Optional[str]
    workspace_name: str
    author_name: str
    total_classes: int = 0
    total_relationships: int = 0
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class DiagramListResponse(BaseModel):
    """List of diagrams"""
    diagrams: List[DiagramResponse]
    total: int
    skip: int
    limit: int


# ============================================================================
# SYNC SCHEMAS
# ============================================================================

class SyncToFalkorDBRequest(BaseModel):
    """Request to sync diagram to FalkorDB"""
    nodes: List[NodeBase]
    edges: List[EdgeBase]


class SyncToFalkorDBResponse(BaseModel):
    """Response from FalkorDB sync"""
    success: bool
    graph_name: str
    nodes_created: int
    edges_created: int
    error: Optional[str] = None