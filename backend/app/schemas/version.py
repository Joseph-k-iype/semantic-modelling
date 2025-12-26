"""
Version control Pydantic schemas
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, UUID4, ConfigDict


class VersionBase(BaseModel):
    """Base version schema"""
    notes: Optional[str] = Field(None, max_length=1000)
    is_major: bool = False


class VersionCreate(VersionBase):
    """Schema for creating a version"""
    model_id: UUID4
    snapshot_data: Dict[str, Any]  # Complete model state


class VersionResponse(VersionBase):
    """Version response schema"""
    id: UUID4
    model_id: UUID4
    version_number: int
    snapshot_data: Dict[str, Any]
    created_by: UUID4
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class VersionCompare(BaseModel):
    """Schema for comparing two versions"""
    version_a_id: UUID4
    version_b_id: UUID4


class VersionDiff(BaseModel):
    """Version difference response"""
    added_elements: List[Dict[str, Any]] = []
    removed_elements: List[Dict[str, Any]] = []
    modified_elements: List[Dict[str, Any]] = []
    summary: Dict[str, int] = {}
    
    model_config = ConfigDict(from_attributes=True)


class VersionRestore(BaseModel):
    """Schema for restoring a version"""
    version_id: UUID4
    create_backup: bool = True


class VersionHistory(BaseModel):
    """Version history response"""
    versions: List[VersionResponse] = []
    total_count: int = 0
    
    model_config = ConfigDict(from_attributes=True)