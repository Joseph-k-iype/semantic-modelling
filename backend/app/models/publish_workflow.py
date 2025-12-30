# backend/app/models/publish_workflow.py
"""
Publish Workflow Database Model - Complete and Fixed
Path: backend/app/models/publish_workflow.py
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
import uuid

from app.db.base import Base


class PublishWorkflow(Base):
    """
    Publish workflow model for managing model publication to common workspace.
    
    This model tracks the approval workflow when users want to promote their
    models from personal/team workspaces to the organization-wide common workspace.
    """
    
    __tablename__ = "publish_workflows"
    
    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    
    # Published entity
    entity_type = Column(String(50), nullable=False, index=True)
    # Supported types: model, diagram
    entity_id = Column(String(36), nullable=False, index=True)
    
    # Source and target workspaces
    source_workspace_id = Column(
        String(36),
        ForeignKey("workspaces.id"),
        nullable=False,
        index=True
    )
    target_workspace_id = Column(
        String(36),
        ForeignKey("workspaces.id"),
        nullable=False,
        index=True
    )
    
    # Workflow status
    status = Column(String(50), nullable=False, default="pending", index=True)
    # Status values: pending, approved, rejected, cancelled
    
    # Request details
    request_message = Column(Text, nullable=True)
    review_message = Column(Text, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    
    # Snapshot of published data at time of request
    # This preserves the exact state that was submitted for approval
    snapshot_data = Column(JSON, nullable=False, default=lambda: {})
    
    # Workflow participants - FIXED: now String(36) to match User model
    requested_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    reviewed_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=True, onupdate=datetime.utcnow)
    reviewed_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    
    # Relationships
    source_workspace = relationship(
        "Workspace",
        foreign_keys=[source_workspace_id],
        backref="outgoing_publish_requests"
    )
    target_workspace = relationship(
        "Workspace",
        foreign_keys=[target_workspace_id],
        backref="incoming_publish_requests"
    )
    requester = relationship(
        "User",
        foreign_keys=[requested_by],
        backref="publish_requests_created"
    )
    reviewer = relationship(
        "User",
        foreign_keys=[reviewed_by],
        backref="publish_requests_reviewed"
    )
    
    def __repr__(self):
        return f"<PublishWorkflow(id={self.id}, status='{self.status}', entity={self.entity_type}:{self.entity_id})>"
    
    @property
    def is_pending(self):
        """Check if workflow is pending review"""
        return self.status == "pending"
    
    @property
    def is_approved(self):
        """Check if workflow has been approved"""
        return self.status == "approved"
    
    @property
    def is_rejected(self):
        """Check if workflow has been rejected"""
        return self.status == "rejected"
    
    @property
    def is_cancelled(self):
        """Check if workflow has been cancelled"""
        return self.status == "cancelled"
    
    @property
    def is_completed(self):
        """Check if workflow has been completed (approved, rejected, or cancelled)"""
        return self.status in ["approved", "rejected", "cancelled"]
    
    @property
    def processing_time(self):
        """Get the time taken to process this workflow request"""
        if self.reviewed_at and self.created_at:
            return (self.reviewed_at - self.created_at).total_seconds()
        return None