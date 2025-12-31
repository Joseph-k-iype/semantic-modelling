# backend/app/schemas/workspace.py
"""
Workspace Pydantic schemas - FIXED for ENUM type compatibility
Path: backend/app/schemas/workspace.py
"""
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, field_serializer
from enum import Enum


class WorkspaceType(str, Enum):
    """Workspace type enumeration - must match database and model"""
    PERSONAL = "personal"
    TEAM = "team"
    COMMON = "common"


class WorkspaceBase(BaseModel):
    """Base workspace schema"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    type: WorkspaceType = WorkspaceType.PERSONAL


class WorkspaceCreate(WorkspaceBase):
    """
    Schema for creating a workspace
    
    FIXED: Properly handles WorkspaceType enum conversion
    """
    pass


class WorkspaceUpdate(BaseModel):
    """Schema for updating a workspace"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None


class WorkspaceResponse(WorkspaceBase):
    """
    Workspace response schema
    
    FIXED: Ensures type is serialized as string value
    """
    id: str
    created_by: str
    settings: Dict[str, Any] = {}
    is_active: bool = True
    created_at: datetime
    updated_at: datetime
    
    @field_serializer('type')
    def serialize_type(self, value: WorkspaceType, _info) -> str:
        """Serialize WorkspaceType enum to string"""
        if isinstance(value, WorkspaceType):
            return value.value
        return str(value)
    
    @field_serializer('id', 'created_by')
    def serialize_uuid(self, value, _info) -> str:
        """Serialize UUID to string"""
        return str(value)
    
    model_config = ConfigDict(
        from_attributes=True,
        use_enum_values=False  # Don't automatically convert enums to values
    )


class WorkspaceMemberRole(str, Enum):
    """Workspace member role enumeration"""
    VIEWER = "viewer"
    EDITOR = "editor"
    PUBLISHER = "publisher"
    ADMIN = "admin"


class WorkspaceMemberBase(BaseModel):
    """Base workspace member schema"""
    user_id: str
    role: WorkspaceMemberRole


class WorkspaceMemberCreate(WorkspaceMemberBase):
    """Schema for adding a workspace member"""
    pass


class WorkspaceMemberUpdate(BaseModel):
    """Schema for updating a workspace member"""
    role: Optional[WorkspaceMemberRole] = None


class WorkspaceMemberResponse(WorkspaceMemberBase):
    """Workspace member response schema"""
    id: str
    workspace_id: str
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class WorkspaceWithMembers(WorkspaceResponse):
    """Workspace response with members"""
    members: list = []
    member_count: int = 0
    
    model_config = ConfigDict(from_attributes=True)