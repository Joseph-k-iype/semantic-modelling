# backend/app/models/publish_workflow.py
"""
Publish Workflow Database Model - COMPLETE AND FIXED
Path: backend/app/models/publish_workflow.py
"""
from datetime import datetime
from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
import enum

from app.db.base import Base


class PublishStatus(str, enum.Enum):
    """Publish request status enumeration"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


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
    
    # Workflow status - Using SQLEnum for PostgreSQL ENUM with proper value handling
    status = Column(
        SQLEnum(
            PublishStatus,
            name="publish_status",
            create_type=False,
            native_enum=False,  # ✅ Use enum values, not names
            values_callable=lambda x: [e.value for e in x]
        ),
        nullable=False,
        default=PublishStatus.PENDING,
        index=True
    )
    
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
        return f"<PublishWorkflow(id={self.id}, status='{self.status.value if isinstance(self.status, PublishStatus) else self.status}', entity_type='{self.entity_type}')>"
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': str(self.id),
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'source_workspace_id': str(self.source_workspace_id),
            'target_workspace_id': str(self.target_workspace_id),
            'status': self.status.value if isinstance(self.status, PublishStatus) else self.status,
            'request_message': self.request_message,
            'review_message': self.review_message,
            'rejection_reason': self.rejection_reason,
            'requested_by': str(self.requested_by),
            'reviewed_by': str(self.reviewed_by) if self.reviewed_by else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None,
            'cancelled_at': self.cancelled_at.isoformat() if self.cancelled_at else None,
        }
    
    @property
    def is_pending(self):
        """Check if workflow is pending approval"""
        return self.status == PublishStatus.PENDING or (isinstance(self.status, str) and self.status == "pending")
    
    @property
    def is_approved(self):
        """Check if workflow was approved"""
        return self.status == PublishStatus.APPROVED or (isinstance(self.status, str) and self.status == "approved")
    
    @property
    def is_rejected(self):
        """Check if workflow was rejected"""
        return self.status == PublishStatus.REJECTED or (isinstance(self.status, str) and self.status == "rejected")
    
    @property
    def is_cancelled(self):
        """Check if workflow was cancelled"""
        return self.status == PublishStatus.CANCELLED or (isinstance(self.status, str) and self.status == "cancelled")
    
    def approve(self, reviewer_id: uuid.UUID, review_message: str = None):
        """Approve the publish request"""
        self.status = PublishStatus.APPROVED
        self.reviewed_by = reviewer_id
        self.review_message = review_message
        self.reviewed_at = datetime.utcnow()
    
    def reject(self, reviewer_id: uuid.UUID, rejection_reason: str):
        """Reject the publish request"""
        self.status = PublishStatus.REJECTED
        self.reviewed_by = reviewer_id
        self.rejection_reason = rejection_reason
        self.reviewed_at = datetime.utcnow()
    
    def cancel(self):
        """Cancel the publish request"""
        self.status = PublishStatus.CANCELLED
        self.cancelled_at = datetime.utcnow()