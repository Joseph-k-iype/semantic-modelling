# backend/app/models/publish_workflow.py
"""
Publish Workflow Database Model - COMPLETE Implementation
Path: backend/app/models/publish_workflow.py

Tracks model publishing requests and approvals for Common Workspace.
"""
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text, Enum as SQLEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
import enum

from app.db.base import Base


class PublishWorkflowStatus(str, enum.Enum):
    """Publish workflow status enumeration"""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class PublishWorkflow(Base):
    """
    Publish workflow model for managing model publishing to Common Workspace
    
    Publishing Flow:
    1. User requests to publish a model from Personal/Team workspace to Common
    2. Admin/Reviewer reviews the request
    3. Request is approved or rejected
    4. On approval, model is published as immutable version
    """
    
    __tablename__ = "publish_workflows"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Source and target
    model_id = Column(UUID(as_uuid=True), ForeignKey("models.id", ondelete="CASCADE"), nullable=False, index=True)
    source_workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    target_workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Request information
    request_title = Column(String(255), nullable=False)
    request_description = Column(Text, nullable=True)
    
    # Version being published
    version_id = Column(UUID(as_uuid=True), ForeignKey("versions.id", ondelete="SET NULL"), nullable=True, index=True)
    version_number = Column(String(20), nullable=True)
    
    # Status
    status = Column(
        SQLEnum(
            PublishWorkflowStatus,
            name="publish_workflow_status",
            create_type=False,
            native_enum=False,
            values_callable=lambda x: [e.value for e in x]
        ),
        nullable=False,
        default=PublishWorkflowStatus.PENDING,
        index=True
    )
    
    # Review information
    review_comments = Column(JSONB, default=list, server_default='[]')  # Array of review comments
    reviewer_notes = Column(Text, nullable=True)
    
    # Approval tracking
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    reviewed_at = Column(DateTime, nullable=True)
    
    # Additional data
    meta_data = Column(JSONB, default=dict, server_default='{}')
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Created by (publisher)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    
    # Relationships
    model = relationship("Model")
    source_workspace = relationship("Workspace", foreign_keys=[source_workspace_id])
    target_workspace = relationship("Workspace", foreign_keys=[target_workspace_id])
    version = relationship("Version")
    requester = relationship("User", foreign_keys=[created_by])
    reviewer = relationship("User", foreign_keys=[reviewed_by])
    
    def __repr__(self):
        return f"<PublishWorkflow(id={self.id}, model_id={self.model_id}, status='{self.status.value}')>"
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': str(self.id),
            'model_id': str(self.model_id),
            'source_workspace_id': str(self.source_workspace_id),
            'target_workspace_id': str(self.target_workspace_id),
            'request_title': self.request_title,
            'request_description': self.request_description,
            'version_id': str(self.version_id) if self.version_id else None,
            'version_number': self.version_number,
            'status': self.status.value,
            'review_comments': self.review_comments,
            'reviewer_notes': self.reviewer_notes,
            'reviewed_by': str(self.reviewed_by) if self.reviewed_by else None,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None,
            'meta_data': self.meta_data,
            'created_by': str(self.created_by),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }