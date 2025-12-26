"""
Model Pydantic schemas
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, UUID4, ConfigDict
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


class ModelStatus(str, Enum):
    """Model status enumeration"""
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class ModelBase(BaseModel):
    """Base model schema"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    type: ModelType


class ModelCreate(ModelBase):
    """Schema for creating a model"""
    workspace_id: UUID4
    folder_id: Optional[UUID4] = None
    tags: List[str] = []
    metadata: dict = {}


class ModelUpdate(BaseModel):
    """Schema for updating a model"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    folder_id: Optional[UUID4] = None
    status: Optional[ModelStatus] = None
    tags: Optional[List[str]] = None
    metadata: Optional[dict] = None


class ModelResponse(ModelBase):
    """Model response schema"""
    id: UUID4
    workspace_id: UUID4
    folder_id: Optional[UUID4] = None
    slug: str
    status: ModelStatus
    version: int
    tags: List[str] = []
    metadata: dict = {}
    created_by: UUID4
    created_at: datetime
    updated_at: datetime
    last_edited_by: Optional[UUID4] = None
    
    model_config = ConfigDict(from_attributes=True)


class ModelWithStats(ModelResponse):
    """Model response with statistics"""
    diagram_count: int = 0
    version_count: int = 0
    comment_count: int = 0
    is_favorited: bool = False
    
    model_config = ConfigDict(from_attributes=True)


class ModelMove(BaseModel):
    """Schema for moving a model to different folder"""
    folder_id: Optional[UUID4] = None


class ModelDuplicate(BaseModel):
    """Schema for duplicating a model"""
    name: str = Field(..., min_length=1, max_length=255)
    workspace_id: Optional[UUID4] = None
    folder_id: Optional[UUID4] = None