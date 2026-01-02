# backend/app/models/workspace_member.py
"""
Workspace Member Database Model - STRATEGIC FIX
Path: backend/app/models/workspace_member.py

CRITICAL FIXES:
- Uses workspace_role enum name (not user_role)
- Matches database schema exactly
- Has all required columns
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
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
    
    STRATEGIC FIX: Uses workspace_role enum (not user_role)
    """
    
    __tablename__ = "workspace_members"
    
    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    
    # Foreign keys
    workspace_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Member role - STRATEGIC FIX: Uses workspace_role enum name
    role = Column(
        SQLEnum(
            WorkspaceMemberRole,
            name="workspace_role",  # ✅ FIXED: workspace_role not user_role
            create_type=False,
            native_enum=False,
            values_callable=lambda x: [e.value for e in x]
        ),
        nullable=False,
        default=WorkspaceMemberRole.VIEWER,
        index=True
    )
    
    # Permissions and settings
    permissions = Column(JSONB, default={}, nullable=False)
    settings = Column(JSONB, default={}, nullable=False)
    meta_data = Column(JSONB, default={}, nullable=False)
    
    # Tracking
    added_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    
    deleted_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    
    # Timestamps
    added_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    last_accessed_at = Column(DateTime, nullable=True, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True, index=True)
    
    # Relationships
    workspace = relationship(
        "Workspace",
        foreign_keys=[workspace_id],
        back_populates="members"
    )
    
    user = relationship(
        "User",
        foreign_keys=[user_id],
        backref="workspace_memberships"
    )
    
    adder = relationship(
        "User",
        foreign_keys=[added_by]
    )
    
    deleter = relationship(
        "User",
        foreign_keys=[deleted_by]
    )
    
    # Unique constraint
    __table_args__ = (
        UniqueConstraint('workspace_id', 'user_id', name='workspace_members_unique'),
    )
    
    def __repr__(self):
        return f"<WorkspaceMember(workspace_id={self.workspace_id}, user_id={self.user_id}, role='{self.role.value}')>"
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': str(self.id),
            'workspace_id': str(self.workspace_id),
            'user_id': str(self.user_id),
            'role': self.role.value,
            'permissions': self.permissions,
            'settings': self.settings,
            'meta_data': self.meta_data,
            'is_active': self.is_active,
            'added_at': self.added_at.isoformat() if self.added_at else None,
            'last_accessed_at': self.last_accessed_at.isoformat() if self.last_accessed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }