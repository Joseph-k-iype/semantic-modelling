# backend/app/models/workspace_member.py
"""
Workspace Member Database Model - COMPLETE AND PRODUCTION READY
Matches database schema: database/postgres/schema/02-workspaces.sql
Path: backend/app/models/workspace_member.py
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Enum as SQLEnum, UniqueConstraint, text
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
    
    Database schema mapping:
    - can_view (NOT can_read)
    - can_edit (NOT can_write)
    - added_at (NOT created_at)
    - added_by (new column)
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
    
    # Member role - Using SQLEnum with proper value handling
    role = Column(
        SQLEnum(
            WorkspaceMemberRole,
            name="user_role",
            create_type=False,
            native_enum=False,  # Use enum values, not names
            values_callable=lambda x: [e.value for e in x]
        ),
        nullable=False,
        default=WorkspaceMemberRole.VIEWER,
        index=True
    )
    
    # Permissions - MATCHES DATABASE: can_view, can_edit (not can_read, can_write)
    can_view = Column(Boolean, nullable=False, default=True)
    can_edit = Column(Boolean, nullable=False, default=False)
    can_delete = Column(Boolean, nullable=False, default=False)
    can_publish = Column(Boolean, nullable=False, default=False)
    can_manage_members = Column(Boolean, nullable=False, default=False)
    
    # Timestamps - MATCHES DATABASE: added_at, added_by (not created_at, updated_at)
    added_at = Column(
        DateTime, 
        nullable=False, 
        default=datetime.utcnow, 
        index=True,
        server_default=text("CURRENT_TIMESTAMP")
    )
    
    added_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Relationships
    workspace = relationship("Workspace", foreign_keys=[workspace_id], backref="members")
    user = relationship("User", foreign_keys=[user_id], backref="workspace_memberships")
    added_by_user = relationship("User", foreign_keys=[added_by])
    
    # Unique constraint
    __table_args__ = (
        UniqueConstraint('workspace_id', 'user_id', name='unique_workspace_member'),
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
            'can_view': self.can_view,
            'can_edit': self.can_edit,
            'can_delete': self.can_delete,
            'can_publish': self.can_publish,
            'can_manage_members': self.can_manage_members,
            'added_at': self.added_at.isoformat() if self.added_at else None,
            'added_by': str(self.added_by) if self.added_by else None,
        }
    
    def has_permission(self, permission: str) -> bool:
        """Check if member has specific permission"""
        permission_map = {
            'view': self.can_view,
            'edit': self.can_edit,
            'delete': self.can_delete,
            'publish': self.can_publish,
            'manage_members': self.can_manage_members,
        }
        return permission_map.get(permission, False)
    
    @classmethod
    def get_permissions_for_role(cls, role: WorkspaceMemberRole) -> dict:
        """Get default permissions for a given role"""
        permissions = {
            WorkspaceMemberRole.VIEWER: {
                'can_view': True,
                'can_edit': False,
                'can_delete': False,
                'can_publish': False,
                'can_manage_members': False,
            },
            WorkspaceMemberRole.EDITOR: {
                'can_view': True,
                'can_edit': True,
                'can_delete': False,
                'can_publish': False,
                'can_manage_members': False,
            },
            WorkspaceMemberRole.PUBLISHER: {
                'can_view': True,
                'can_edit': True,
                'can_delete': False,
                'can_publish': True,
                'can_manage_members': False,
            },
            WorkspaceMemberRole.ADMIN: {
                'can_view': True,
                'can_edit': True,
                'can_delete': True,
                'can_publish': True,
                'can_manage_members': True,
            },
        }
        return permissions.get(role, permissions[WorkspaceMemberRole.VIEWER])