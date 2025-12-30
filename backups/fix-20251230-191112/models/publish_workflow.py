# backend/app/models/publish_workflow.py
"""
Publish Workflow Database Model - COMPLETE AND FIXED
Path: backend/app/models/publish_workflow.py
"""
from datetime import datetime
from sqlalchemy import Column, String, Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
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
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    
    # Published entity
    entity_type = Column(String(50), nullable=False, index=True)
    # Supported types: model, diagram
    entity_id = Column(String(255), nullable=False, index=True)
    
    # Source and target workspaces
    source_workspace_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    target_workspace_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
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
    snapshot_data = Column(JSONB, nullable=False, default=dict)
    
    # Workflow participants
    requested_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    reviewed_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Timestamps
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True
    )
    updated_at = Column(
        DateTime,
        nullable=True,
        onupdate=datetime.utcnow
    )
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
        return f"<PublishWorkflow(id={self.id}, status='{self.status}', entity_type='{self.entity_type}')>"
    
    @property
    def is_pending(self):
        """Check if workflow is pending approval"""
        return self.status == "pending"
    
    @property
    def is_approved(self):
        """Check if workflow was approved"""
        return self.status == "approved"
    
    @property
    def is_rejected(self):
        """Check if workflow was rejected"""
        return self.status == "rejected"
    
    @property
    def is_cancelled(self):
        """Check if workflow was cancelled"""
        return self.status == "cancelled"
    
    def approve(self, reviewer_id: uuid.UUID, review_message: str = None):
        """Approve the publish request"""
        self.status = "approved"
        self.reviewed_by = reviewer_id
        self.review_message = review_message
        self.reviewed_at = datetime.utcnow()
    
    def reject(self, reviewer_id: uuid.UUID, rejection_reason: str):
        """Reject the publish request"""
        self.status = "rejected"
        self.reviewed_by = reviewer_id
        self.rejection_reason = rejection_reason
        self.reviewed_at = datetime.utcnow()
    
    def cancel(self):
        """Cancel the publish request"""
        self.status = "cancelled"
        self.cancelled_at = datetime.utcnow()