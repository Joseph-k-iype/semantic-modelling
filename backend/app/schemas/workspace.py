"""
Workspace Pydantic schemas - Matching actual database models
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class WorkspaceType(str, Enum):
    """Workspace type enumeration"""
    PERSONAL = "personal"
    TEAM = "team"
    COMMON = "common"


class WorkspaceBase(BaseModel):
    """Base workspace schema"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    type: WorkspaceType = WorkspaceType.PERSONAL


class WorkspaceCreate(WorkspaceBase):
    """Schema for creating a workspace"""
    pass


class WorkspaceUpdate(BaseModel):
    """Schema for updating a workspace"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None


class WorkspaceResponse(WorkspaceBase):
    """Workspace response schema"""
    id: str
    created_by: str
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


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