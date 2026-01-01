# backend/app/models/audit_log.py
"""
Audit Log Database Model - COMPLETE Implementation
Path: backend/app/models/audit_log.py

Comprehensive audit logging for all system actions.
"""
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text, Enum as SQLEnum, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.orm import relationship
import uuid
import enum

from app.db.base import Base


class AuditLogAction(str, enum.Enum):
    """Audit log action types"""
    # User actions
    USER_LOGIN = "USER_LOGIN"
    USER_LOGOUT = "USER_LOGOUT"
    USER_REGISTER = "USER_REGISTER"
    USER_UPDATE = "USER_UPDATE"
    USER_DELETE = "USER_DELETE"
    
    # Workspace actions
    WORKSPACE_CREATE = "WORKSPACE_CREATE"
    WORKSPACE_UPDATE = "WORKSPACE_UPDATE"
    WORKSPACE_DELETE = "WORKSPACE_DELETE"
    WORKSPACE_MEMBER_ADD = "WORKSPACE_MEMBER_ADD"
    WORKSPACE_MEMBER_REMOVE = "WORKSPACE_MEMBER_REMOVE"
    WORKSPACE_MEMBER_UPDATE = "WORKSPACE_MEMBER_UPDATE"
    
    # Model actions
    MODEL_CREATE = "MODEL_CREATE"
    MODEL_UPDATE = "MODEL_UPDATE"
    MODEL_DELETE = "MODEL_DELETE"
    MODEL_PUBLISH = "MODEL_PUBLISH"
    MODEL_VERSION_CREATE = "MODEL_VERSION_CREATE"
    
    # Diagram actions
    DIAGRAM_CREATE = "DIAGRAM_CREATE"
    DIAGRAM_UPDATE = "DIAGRAM_UPDATE"
    DIAGRAM_DELETE = "DIAGRAM_DELETE"
    DIAGRAM_EXPORT = "DIAGRAM_EXPORT"
    
    # Folder actions
    FOLDER_CREATE = "FOLDER_CREATE"
    FOLDER_UPDATE = "FOLDER_UPDATE"
    FOLDER_DELETE = "FOLDER_DELETE"
    FOLDER_MOVE = "FOLDER_MOVE"
    
    # Layout actions
    LAYOUT_CREATE = "LAYOUT_CREATE"
    LAYOUT_UPDATE = "LAYOUT_UPDATE"
    LAYOUT_DELETE = "LAYOUT_DELETE"
    LAYOUT_APPLY = "LAYOUT_APPLY"
    
    # Comment actions
    COMMENT_CREATE = "COMMENT_CREATE"
    COMMENT_UPDATE = "COMMENT_UPDATE"
    COMMENT_DELETE = "COMMENT_DELETE"
    COMMENT_RESOLVE = "COMMENT_RESOLVE"
    
    # Publish workflow actions
    PUBLISH_REQUEST_CREATE = "PUBLISH_REQUEST_CREATE"
    PUBLISH_REQUEST_APPROVE = "PUBLISH_REQUEST_APPROVE"
    PUBLISH_REQUEST_REJECT = "PUBLISH_REQUEST_REJECT"
    PUBLISH_REQUEST_CANCEL = "PUBLISH_REQUEST_CANCEL"
    
    # Security actions
    PASSWORD_CHANGE = "PASSWORD_CHANGE"
    PASSWORD_RESET = "PASSWORD_RESET"
    TOKEN_REFRESH = "TOKEN_REFRESH"
    PERMISSION_CHANGE = "PERMISSION_CHANGE"


class AuditLog(Base):
    """
    Audit log model for tracking all system actions
    
    Provides comprehensive audit trail for compliance and debugging.
    Logs who did what, when, where, and what changed.
    """
    
    __tablename__ = "audit_logs"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Action information
    action = Column(
        SQLEnum(
            AuditLogAction,
            name="audit_log_action",
            create_type=False,
            native_enum=False,
            values_callable=lambda x: [e.value for e in x]
        ),
        nullable=False,
        index=True
    )
    
    # Entity reference (polymorphic)
    entity_type = Column(String(50), nullable=True, index=True)  # e.g., "MODEL", "WORKSPACE"
    entity_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    # Actor (who performed the action)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Request metadata
    ip_address = Column(INET, nullable=True)
    user_agent = Column(Text, nullable=True)
    request_id = Column(String(255), nullable=True, index=True)  # For correlating related actions
    
    # Change tracking
    old_values = Column(JSONB, nullable=True)  # State before action
    new_values = Column(JSONB, nullable=True)  # State after action
    changes = Column(JSONB, nullable=True)  # Summary of what changed
    
    # Additional context
    meta_data = Column(JSONB, default=dict, server_default='{}')
    
    # Result
    success = Column(Boolean, default=True, nullable=False, index=True)
    error_message = Column(Text, nullable=True)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Composite indexes for common queries
    __table_args__ = (
        Index('idx_audit_logs_user_action', 'user_id', 'action'),
        Index('idx_audit_logs_entity', 'entity_type', 'entity_id'),
        Index('idx_audit_logs_created_at_desc', created_at.desc()),
        Index('idx_audit_logs_action_created_at', 'action', 'created_at'),
    )
    
    # Relationships
    user = relationship("User")
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, action='{self.action.value}', user_id={self.user_id})>"
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': str(self.id),
            'action': self.action.value,
            'entity_type': self.entity_type,
            'entity_id': str(self.entity_id) if self.entity_id else None,
            'user_id': str(self.user_id) if self.user_id else None,
            'ip_address': str(self.ip_address) if self.ip_address else None,
            'user_agent': self.user_agent,
            'request_id': self.request_id,
            'old_values': self.old_values,
            'new_values': self.new_values,
            'changes': self.changes,
            'meta_data': self.meta_data,
            'success': self.success,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }