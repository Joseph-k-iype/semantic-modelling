# backend/app/models/audit_log.py
"""
Audit Log Database Model - MATCHES database/postgres/schema/10-audit_logs.sql EXACTLY
Path: backend/app/models/audit_log.py
"""
from datetime import datetime
from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.orm import relationship
import uuid

from app.db.base import Base


class AuditLog(Base):
    """
    Audit log model for tracking all system actions
    
    CRITICAL: Matches database/postgres/schema/10-audit_logs.sql EXACTLY
    """
    
    __tablename__ = "audit_logs"
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    
    # Who performed the action
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    user_email = Column(String(255), nullable=True)  # Denormalized for deleted users
    
    # What was done
    action = Column(String(100), nullable=False, index=True)  # Uses audit_action enum in DB
    entity_type = Column(String(100), nullable=True, index=True)
    entity_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    # Detailed changes
    old_values = Column(JSONB, nullable=True)
    new_values = Column(JSONB, nullable=True)
    
    # Context
    workspace_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # Request details
    ip_address = Column(INET, nullable=True, index=True)
    user_agent = Column(Text, nullable=True)
    request_id = Column(String(100), nullable=True, index=True)
    
    # Timestamp
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True
    )
    
    # Additional metadata - using meta_data to avoid SQLAlchemy's reserved 'metadata'
    meta_data = Column('metadata', JSONB, nullable=True, default=dict)
    
    # Success or failure
    success = Column(Boolean, nullable=True, default=True)
    error_message = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], backref="audit_logs")
    workspace = relationship("Workspace", foreign_keys=[workspace_id], backref="audit_logs")
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, action='{self.action}', entity_type='{self.entity_type}')>"
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id) if self.user_id else None,
            'user_email': self.user_email,
            'action': self.action,
            'entity_type': self.entity_type,
            'entity_id': str(self.entity_id) if self.entity_id else None,
            'old_values': self.old_values,
            'new_values': self.new_values,
            'workspace_id': str(self.workspace_id) if self.workspace_id else None,
            'ip_address': str(self.ip_address) if self.ip_address else None,
            'user_agent': self.user_agent,
            'request_id': self.request_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'metadata': self.meta_data,
            'success': self.success,
            'error_message': self.error_message,
        }
    
    @property
    def is_create_action(self):
        """Check if this is a create action"""
        return self.action == "create"
    
    @property
    def is_update_action(self):
        """Check if this is an update action"""
        return self.action == "update"
    
    @property
    def is_delete_action(self):
        """Check if this is a delete action"""
        return self.action == "delete"
    
    @property
    def is_publish_action(self):
        """Check if this is a publish action"""
        return self.action in ["publish_request", "publish_approve", "publish_reject"]
    
    @property
    def is_successful(self):
        """Check if the action was successful"""
        return self.success is True