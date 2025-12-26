"""
Diagram Pydantic schemas
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, UUID4, ConfigDict


class DiagramBase(BaseModel):
    """Base diagram schema"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class DiagramCreate(DiagramBase):
    """Schema for creating a diagram"""
    model_id: UUID4
    notation_type: str = Field(..., max_length=50)
    content: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}


class DiagramUpdate(BaseModel):
    """Schema for updating a diagram"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    content: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class DiagramResponse(DiagramBase):
    """Diagram response schema"""
    id: UUID4
    model_id: UUID4
    notation_type: str
    content: Dict[str, Any]
    metadata: Dict[str, Any]
    version: int
    created_by: UUID4
    created_at: datetime
    updated_at: datetime
    last_edited_by: Optional[UUID4] = None
    
    model_config = ConfigDict(from_attributes=True)


class DiagramWithLayouts(DiagramResponse):
    """Diagram response with layouts"""
    layouts: List[Any] = []  # Will be replaced with LayoutResponse when available
    
    model_config = ConfigDict(from_attributes=True)


class DiagramDuplicate(BaseModel):
    """Schema for duplicating a diagram"""
    name: str = Field(..., min_length=1, max_length=255)
    model_id: Optional[UUID4] = None