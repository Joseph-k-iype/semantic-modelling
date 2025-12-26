"""
Publish workflow Pydantic schemas
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, UUID4, ConfigDict
from enum import Enum


class PublishStatus(str, Enum):
    """Publish request status enumeration"""
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class PublishRequestBase(BaseModel):
    """Base publish request schema"""
    message: Optional[str] = Field(None, max_length=1000)


class PublishRequestCreate(PublishRequestBase):
    """Schema for creating a publish request"""
    model_id: UUID4
    target_workspace_id: UUID4
    version_notes: Optional[str] = None


class PublishRequestUpdate(BaseModel):
    """Schema for updating a publish request"""
    message: Optional[str] = Field(None, max_length=1000)
    status: Optional[PublishStatus] = None


class PublishRequestResponse(PublishRequestBase):
    """Publish request response schema"""
    id: UUID4
    model_id: UUID4
    source_workspace_id: UUID4
    target_workspace_id: UUID4
    status: PublishStatus
    version_notes: Optional[str] = None
    requested_by: UUID4
    requested_at: datetime
    reviewed_by: Optional[UUID4] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class PublishReview(BaseModel):
    """Schema for reviewing a publish request"""
    approve: bool
    notes: Optional[str] = Field(None, max_length=1000)


class PublishApproval(BaseModel):
    """Schema for publish approval"""
    request_id: UUID4
    notes: Optional[str] = None


class PublishHistory(BaseModel):
    """Schema for publish history"""
    requests: List[PublishRequestResponse] = []
    total_count: int = 0
    
    model_config = ConfigDict(from_attributes=True)