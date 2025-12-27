"""
Diagram Pydantic schemas - Matching actual database models
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class DiagramType(str, Enum):
    """Diagram type enumeration"""
    ER = "er"
    UML_CLASS = "uml_class"
    UML_SEQUENCE = "uml_sequence"
    UML_ACTIVITY = "uml_activity"
    UML_STATE_MACHINE = "uml_state_machine"
    UML_COMPONENT = "uml_component"
    UML_DEPLOYMENT = "uml_deployment"
    UML_PACKAGE = "uml_package"
    BPMN = "bpmn"


class DiagramBase(BaseModel):
    """Base diagram schema"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    type: str  # Can be DiagramType enum value


class DiagramCreate(DiagramBase):
    """Schema for creating a diagram"""
    workspace_id: str
    model_id: Optional[str] = None
    folder_id: Optional[str] = None
    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []
    viewport: Dict[str, Any] = Field(default={"x": 0, "y": 0, "zoom": 1})
    metadata: Dict[str, Any] = {}


class DiagramUpdate(BaseModel):
    """Schema for updating a diagram"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    model_id: Optional[str] = None
    folder_id: Optional[str] = None
    nodes: Optional[List[Dict[str, Any]]] = None
    edges: Optional[List[Dict[str, Any]]] = None
    viewport: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class DiagramResponse(DiagramBase):
    """Diagram response schema"""
    id: str
    workspace_id: str
    model_id: Optional[str] = None
    folder_id: Optional[str] = None
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    viewport: Dict[str, Any]
    metadata: Dict[str, Any]
    created_by: str
    created_at: datetime
    updated_at: datetime
    updated_by: str
    deleted_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class DiagramWithLayouts(DiagramResponse):
    """Diagram response with available layouts"""
    available_layouts: List[str] = []
    
    model_config = ConfigDict(from_attributes=True)


class DiagramDuplicate(BaseModel):
    """Schema for duplicating a diagram"""
    name: str = Field(..., min_length=1, max_length=255)
    workspace_id: Optional[str] = None
    model_id: Optional[str] = None
    folder_id: Optional[str] = None