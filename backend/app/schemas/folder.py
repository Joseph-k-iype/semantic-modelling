"""
Folder Pydantic schemas
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, UUID4, ConfigDict


class FolderBase(BaseModel):
    """Base folder schema"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    color: Optional[str] = Field(None, max_length=7, pattern=r'^#[0-9A-Fa-f]{6}$')
    icon: Optional[str] = Field(None, max_length=50)


class FolderCreate(FolderBase):
    """Schema for creating a folder"""
    workspace_id: UUID4
    parent_id: Optional[UUID4] = None
    position: int = 0


class FolderUpdate(BaseModel):
    """Schema for updating a folder"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    color: Optional[str] = Field(None, max_length=7, pattern=r'^#[0-9A-Fa-f]{6}$')
    icon: Optional[str] = Field(None, max_length=50)
    parent_id: Optional[UUID4] = None
    position: Optional[int] = None


class FolderMove(BaseModel):
    """Schema for moving a folder"""
    parent_id: Optional[UUID4] = None
    position: int = 0


class FolderResponse(FolderBase):
    """Folder response schema"""
    id: UUID4
    workspace_id: UUID4
    parent_id: Optional[UUID4] = None
    path: str
    depth: int
    position: int
    created_by: UUID4
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class FolderTree(FolderResponse):
    """Folder tree schema with children"""
    children: List['FolderTree'] = []
    model_count: int = 0
    
    model_config = ConfigDict(from_attributes=True)


class FolderWithModels(FolderResponse):
    """Folder with model count"""
    model_count: int = 0
    
    model_config = ConfigDict(from_attributes=True)