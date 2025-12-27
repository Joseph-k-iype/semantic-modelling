"""
Folder Pydantic schemas - Matching actual database models
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class FolderBase(BaseModel):
    """Base folder schema"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class FolderCreate(FolderBase):
    """Schema for creating a folder"""
    workspace_id: str
    parent_id: Optional[str] = None


class FolderUpdate(BaseModel):
    """Schema for updating a folder"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    parent_id: Optional[str] = None


class FolderMove(BaseModel):
    """Schema for moving a folder"""
    parent_id: Optional[str] = None


class FolderResponse(FolderBase):
    """Folder response schema"""
    id: str
    workspace_id: str
    parent_folder_id: Optional[str] = None
    created_by: str
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class FolderTree(FolderResponse):
    """Folder tree schema with children"""
    children: list = []
    model_count: int = 0
    
    model_config = ConfigDict(from_attributes=True)


class FolderWithModels(FolderResponse):
    """Folder with model count"""
    model_count: int = 0
    
    model_config = ConfigDict(from_attributes=True)