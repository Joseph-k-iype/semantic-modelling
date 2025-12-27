# backend/app/schemas/diagram.py
"""
Diagram Pydantic Schemas
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class DiagramBase(BaseModel):
    """Base diagram schema"""
    name: str = Field(..., min_length=1, max_length=255)
    type: str = Field(..., description="Diagram type (ER, UML_CLASS, BPMN, etc.)")
    description: Optional[str] = None


class DiagramCreate(DiagramBase):
    """Schema for creating a diagram"""
    model_id: str = Field(..., description="ID of the parent model")


class DiagramUpdate(BaseModel):
    """Schema for updating a diagram"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    nodes: Optional[List[Dict[str, Any]]] = None
    edges: Optional[List[Dict[str, Any]]] = None
    viewport: Optional[Dict[str, Any]] = None


class DiagramSaveRequest(BaseModel):
    """Schema for saving diagram state"""
    nodes: List[Dict[str, Any]] = Field(..., description="List of diagram nodes")
    edges: List[Dict[str, Any]] = Field(..., description="List of diagram edges")
    viewport: Optional[Dict[str, Any]] = Field(
        default={"x": 0, "y": 0, "zoom": 1},
        description="Viewport state"
    )


class DiagramResponse(DiagramBase):
    """Schema for diagram response"""
    id: str
    model_id: str
    nodes: List[Dict[str, Any]] = Field(default_factory=list)
    edges: List[Dict[str, Any]] = Field(default_factory=list)
    viewport: Dict[str, Any] = Field(default_factory=lambda: {"x": 0, "y": 0, "zoom": 1})
    created_by: str
    updated_by: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class DiagramWithLayouts(DiagramResponse):
    """Diagram response with layout information"""
    layouts: List[Dict[str, Any]] = Field(default_factory=list)
    default_layout_id: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class DiagramDuplicate(BaseModel):
    """Schema for duplicating a diagram"""
    new_name: str = Field(..., min_length=1, max_length=255)
    copy_layouts: bool = Field(default=True, description="Whether to copy layouts")
    target_model_id: Optional[str] = Field(None, description="Target model ID (if different)")


class DiagramLineageRequest(BaseModel):
    """Schema for lineage request"""
    node_id: str = Field(..., description="Node ID to get lineage for")
    direction: str = Field(
        default="both",
        description="Lineage direction: 'upstream', 'downstream', or 'both'"
    )
    depth: int = Field(default=3, ge=1, le=10, description="Maximum traversal depth")


class DiagramLineageResponse(BaseModel):
    """Schema for lineage response"""
    node_id: str
    direction: str
    lineage: List[Dict[str, Any]]


# Node Data Schemas
class NodeData(BaseModel):
    """Base node data schema"""
    label: str
    description: Optional[str] = None


class EREntityData(NodeData):
    """ER Entity node data"""
    entity: Optional[Dict[str, Any]] = None
    attributes: List[Dict[str, Any]] = Field(default_factory=list)


class UMLClassData(NodeData):
    """UML Class node data"""
    class_: Optional[Dict[str, Any]] = Field(None, alias="class")
    attributes: List[Dict[str, Any]] = Field(default_factory=list)
    methods: List[Dict[str, Any]] = Field(default_factory=list)
    is_abstract: bool = False
    stereotype: Optional[str] = None


class BPMNTaskData(NodeData):
    """BPMN Task node data"""
    task: Optional[Dict[str, Any]] = None
    task_type: Optional[str] = None  # user, service, manual, etc.


class BPMNEventData(NodeData):
    """BPMN Event node data"""
    event: Optional[Dict[str, Any]] = None
    event_type: Optional[str] = None  # start, end, intermediate


class BPMNGatewayData(NodeData):
    """BPMN Gateway node data"""
    gateway: Optional[Dict[str, Any]] = None
    gateway_type: Optional[str] = None  # exclusive, parallel, inclusive


class DiagramNode(BaseModel):
    """Schema for diagram node"""
    id: str
    type: str
    data: Dict[str, Any]
    position: Dict[str, float]
    width: Optional[float] = None
    height: Optional[float] = None


class DiagramEdge(BaseModel):
    """Schema for diagram edge"""
    id: str
    type: str
    source: str
    target: str
    data: Optional[Dict[str, Any]] = None
    sourceHandle: Optional[str] = None
    targetHandle: Optional[str] = None
    label: Optional[str] = None