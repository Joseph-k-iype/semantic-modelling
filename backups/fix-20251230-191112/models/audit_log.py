# backend/app/models/audit_log.py
"""
Audit Log Database Model - COMPLETE AND FIXED
Path: backend/app/models/audit_log.py
"""
from datetime import datetime
from sqlalchemy import Column, String, Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

from app.db.base import Base


class AuditLog(Base):
    """Audit log model for tracking all system actions"""
    
    __tablename__ = "audit_logs"
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    
    # Action details
    action = Column(String(100), nullable=False, index=True)
    # Supported actions: create, update, delete, publish, approve, reject, etc.
    
    entity_type = Column(String(50), nullable=False, index=True)
    # Supported types: user, workspace, folder, model, diagram, comment, etc.
    
    entity_id = Column(String(255), nullable=False, index=True)
    
    # User who performed the action
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # Workspace context
    workspace_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # Action details
    description = Column(Text, nullable=True)
    
    # Metadata - stores additional context as JSON
    metadata_col = Column('metadata', JSONB, nullable=False, default=dict)
    
    # Changes made (for update actions)
    changes = Column(JSONB, nullable=True)
    # Format: {"field_name": {"old": "old_value", "new": "new_value"}}
    
    # Request context
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    user_agent = Column(Text, nullable=True)
    
    # Timestamp
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True
    )
    
    # Relationships
    user = relationship("User", backref="audit_logs")
    workspace = relationship("Workspace", backref="audit_logs")
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, action='{self.action}', entity_type='{self.entity_type}')>"
    
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
        return self.action in ["publish", "approve", "reject"]