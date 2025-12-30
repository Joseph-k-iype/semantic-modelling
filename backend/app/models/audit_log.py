# backend/app/models/audit_log.py
"""
Audit Log Database Model - Complete and Fixed
Path: backend/app/models/audit_log.py
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
import uuid

from app.db.base import Base


class AuditLog(Base):
    """Audit log model for tracking all system actions"""
    
    __tablename__ = "audit_logs"
    
    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    
    # Action details
    action = Column(String(100), nullable=False, index=True)
    # Supported actions: create, update, delete, publish, approve, reject, etc.
    
    entity_type = Column(String(50), nullable=False, index=True)
    # Supported types: user, workspace, folder, model, diagram, comment, etc.
    
    entity_id = Column(String(36), nullable=False, index=True)
    
    # Action result
    success = Column(String(10), nullable=False, default="success", index=True)
    # Values: success, failure, error
    
    error_message = Column(Text, nullable=True)
    
    # Change details - what was changed
    changes = Column(JSON, nullable=True, default=lambda: {})
    # Example: {"field": "name", "old_value": "Old Name", "new_value": "New Name"}
    
    # Additional metadata about the action
    # FIXED: Use meta_data as Python attribute, 'metadata' as DB column name
    meta_data = Column('metadata', JSON, nullable=True, default=lambda: {})
    
    # Request details for tracking
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    user_agent = Column(Text, nullable=True)
    request_id = Column(String(100), nullable=True, index=True)  # For request tracking
    
    # Session information
    session_id = Column(String(100), nullable=True, index=True)
    
    # Audit - FIXED: now String(36) to match User model
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    # nullable=True because some actions might be system-generated
    
    # Relationships
    user = relationship("User", foreign_keys=[created_by], backref="audit_logs")
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, action={self.action}, entity={self.entity_type}:{self.entity_id}, success={self.success})>"
    
    @property
    def is_success(self):
        """Check if action was successful"""
        return self.success == "success"
    
    @property
    def is_failure(self):
        """Check if action failed"""
        return self.success in ["failure", "error"]
    
    @property
    def has_changes(self):
        """Check if this audit log records any changes"""
        return bool(self.changes)
    
    @property
    def change_count(self):
        """Get the number of changes recorded"""
        return len(self.changes) if isinstance(self.changes, dict) else 0