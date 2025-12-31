# backend/app/models/workspace_member.py
"""
Workspace Member Database Model - For workspace collaboration
Path: backend/app/models/workspace_member.py
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
import enum

from app.db.base import Base


class WorkspaceMemberRole(str, enum.Enum):
    """Workspace member role enumeration"""
    VIEWER = "viewer"
    EDITOR = "editor"
    PUBLISHER = "publisher"
    ADMIN = "admin"


class WorkspaceMember(Base):
    """
    Workspace member model - manages user access to workspaces
    """
    
    __tablename__ = "workspace_members"
    
    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    
    # Workspace relationship
    workspace_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # User relationship
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Member role - Using SQLEnum for PostgreSQL ENUM
    role = Column(
        SQLEnum(WorkspaceMemberRole, name="user_role", create_type=False),
        nullable=False,
        default=WorkspaceMemberRole.VIEWER,
        index=True
    )
    
    # Permissions (optional fine-grained control)
    can_read = Column(Boolean, nullable=False, default=True)
    can_write = Column(Boolean, nullable=False, default=False)
    can_delete = Column(Boolean, nullable=False, default=False)
    can_publish = Column(Boolean, nullable=False, default=False)
    can_manage_members = Column(Boolean, nullable=False, default=False)
    
    # Status
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    workspace = relationship("Workspace", back_populates="members")
    user = relationship("User", back_populates="workspace_memberships")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('workspace_id', 'user_id', name='unique_workspace_user'),
    )
    
    def __repr__(self):
        return f"<WorkspaceMember(workspace_id={self.workspace_id}, user_id={self.user_id}, role='{self.role.value}')>"
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': str(self.id),
            'workspace_id': str(self.workspace_id),
            'user_id': str(self.user_id),
            'role': self.role.value if isinstance(self.role, WorkspaceMemberRole) else self.role,
            'can_read': self.can_read,
            'can_write': self.can_write,
            'can_delete': self.can_delete,
            'can_publish': self.can_publish,
            'can_manage_members': self.can_manage_members,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }