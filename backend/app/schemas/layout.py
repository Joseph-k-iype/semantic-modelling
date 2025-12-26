"""
Layout Pydantic schemas
"""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, UUID4, ConfigDict
from enum import Enum


class LayoutEngine(str, Enum):
    """Layout engine enumeration"""
    MANUAL = "manual"
    LAYERED = "layered"
    FORCE_DIRECTED = "force_directed"
    BPMN_SWIMLANE = "bpmn_swimlane"
    UML_SEQUENCE = "uml_sequence"
    STATE_MACHINE = "state_machine"


class LayoutBase(BaseModel):
    """Base layout schema"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    engine: LayoutEngine = LayoutEngine.MANUAL


class LayoutCreate(LayoutBase):
    """Schema for creating a layout"""
    diagram_id: UUID4
    data: Dict[str, Any] = {}  # Node positions, edge routing, etc.
    constraints: Dict[str, Any] = {}  # Pinned nodes, locked sections, etc.
    settings: Dict[str, Any] = {}  # Engine-specific settings


class LayoutUpdate(BaseModel):
    """Schema for updating a layout"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    constraints: Optional[Dict[str, Any]] = None
    settings: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class LayoutResponse(LayoutBase):
    """Layout response schema"""
    id: UUID4
    diagram_id: UUID4
    data: Dict[str, Any]
    constraints: Dict[str, Any]
    settings: Dict[str, Any]
    is_active: bool
    created_by: UUID4
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class LayoutApply(BaseModel):
    """Schema for applying a layout"""
    layout_id: UUID4
    preserve_manual_positions: bool = True


class LayoutCompute(BaseModel):
    """Schema for computing a new layout"""
    engine: LayoutEngine
    constraints: Dict[str, Any] = {}
    settings: Dict[str, Any] = {}