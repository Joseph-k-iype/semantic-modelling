"""
Model Pydantic schemas - Matching actual database models
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class ModelType(str, Enum):
    """Model type enumeration"""
    ER = "er"
    UML_CLASS = "uml_class"
    UML_SEQUENCE = "uml_sequence"
    UML_ACTIVITY = "uml_activity"
    UML_STATE_MACHINE = "uml_state_machine"
    UML_COMPONENT = "uml_component"
    UML_DEPLOYMENT = "uml_deployment"
    UML_PACKAGE = "uml_package"
    BPMN = "bpmn"


class ModelBase(BaseModel):
    """Base model schema"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    type: ModelType


class ModelCreate(ModelBase):
    """Schema for creating a model"""
    workspace_id: str
    folder_id: Optional[str] = None
    metadata: dict = {}


class ModelUpdate(BaseModel):
    """Schema for updating a model"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    folder_id: Optional[str] = None
    metadata: Optional[dict] = None


class ModelResponse(ModelBase):
    """Model response schema"""
    id: str
    workspace_id: str
    folder_id: Optional[str] = None
    metadata: dict
    created_by: str
    created_at: datetime
    updated_at: datetime
    updated_by: str
    
    model_config = ConfigDict(from_attributes=True)


class ModelWithStats(ModelResponse):
    """Model response with statistics"""
    diagram_count: int = 0
    
    model_config = ConfigDict(from_attributes=True)


class ModelMove(BaseModel):
    """Schema for moving a model to different folder"""
    folder_id: Optional[str] = None


class ModelDuplicate(BaseModel):
    """Schema for duplicating a model"""
    name: str = Field(..., min_length=1, max_length=255)
    workspace_id: Optional[str] = None
    folder_id: Optional[str] = None


# For backwards compatibility with existing imports
ModelStatus = str  # Not used in current models