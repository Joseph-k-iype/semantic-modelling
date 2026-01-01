# backend/app/models/workspace.py
"""
Workspace Database Models - COMPLETE Implementation
Path: backend/app/models/workspace.py

Models:
- Workspace: Main workspace entity
- WorkspaceMember: User membership in workspace
- WorkspaceInvitation: Pending workspace invitations
"""
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text, Enum as SQLEnum, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
import enum

from app.db.base import Base


class WorkspaceType(str, enum.Enum):
    """Workspace type enumeration - MUST match database ENUM 'workspace_type'"""
    PERSONAL = "PERSONAL"
    TEAM = "TEAM"
    COMMON = "COMMON"


class WorkspaceRole(str, enum.Enum):
    """Workspace member role enumeration - MUST match database ENUM 'workspace_role'"""
    VIEWER = "VIEWER"
    EDITOR = "EDITOR"
    PUBLISHER = "PUBLISHER"
    ADMIN = "ADMIN"


class InvitationStatus(str, enum.Enum):
    """Invitation status enumeration - MUST match database ENUM 'invitation_status'"""
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class Workspace(Base):
    """
    Workspace model for organizing models and collaboration
    
    Workspace Types:
    - PERSONAL: User's private workspace
    - TEAM: Shared workspace for teams
    - COMMON: Organization-wide workspace
    """
    
    __tablename__ = "workspaces"
    
    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    
    # Basic information
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Workspace type
    type = Column(
        SQLEnum(
            WorkspaceType,
            name="workspace_type",
            create_type=False,
            native_enum=False,
            values_callable=lambda x: [e.value for e in x]
        ),
        nullable=False,
        default=WorkspaceType.PERSONAL,
        index=True
    )
    
    # Owner (user who created the workspace)
    owner_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    
    # Settings and metadata
    settings = Column(JSONB, nullable=False, default=dict, server_default='{}')
    meta_data = Column(JSONB, nullable=False, default=dict, server_default='{}')
    
    # Icon and color for UI
    icon = Column(String(50), nullable=True)
    color = Column(String(7), nullable=True)  # Hex color code
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_archived = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    deleted_at = Column(DateTime, nullable=True, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Audit trail
    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    updated_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # Relationships
    owner = relationship("User", foreign_keys=[owner_id])
    members = relationship("WorkspaceMember", back_populates="workspace", cascade="all, delete-orphan")
    folders = relationship("Folder", back_populates="workspace", cascade="all, delete-orphan")
    models = relationship("Model", back_populates="workspace", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Workspace(id={self.id}, name='{self.name}', type='{self.type.value}')>"
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': str(self.id),
            'name': self.name,
            'slug': self.slug,
            'description': self.description,
            'type': self.type.value,
            'owner_id': str(self.owner_id),
            'icon': self.icon,
            'color': self.color,
            'is_active': self.is_active,
            'is_archived': self.is_archived,
            'settings': self.settings,
            'meta_data': self.meta_data,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class WorkspaceMember(Base):
    """
    Workspace member model for tracking user access to workspaces
    
    Roles:
    - VIEWER: Can view models and diagrams
    - EDITOR: Can edit models and diagrams
    - PUBLISHER: Can publish models to common workspace
    - ADMIN: Full workspace management permissions
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
    
    # Role in workspace
    role = Column(
        SQLEnum(
            WorkspaceRole,
            name="workspace_role",
            create_type=False,
            native_enum=False,
            values_callable=lambda x: [e.value for e in x]
        ),
        nullable=False,
        default=WorkspaceRole.VIEWER,
        index=True
    )
    
    # Invitation details
    invited_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    
    invited_at = Column(DateTime, nullable=True)
    joined_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    
    # Timestamps
    deleted_at = Column(DateTime, nullable=True, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Unique constraint: one membership per user per workspace
    __table_args__ = (
        UniqueConstraint('workspace_id', 'user_id', 'deleted_at', name='unique_workspace_member'),
    )
    
    # Relationships
    workspace = relationship("Workspace", back_populates="members")
    user = relationship("User", foreign_keys=[user_id])
    inviter = relationship("User", foreign_keys=[invited_by])
    
    def __repr__(self):
        return f"<WorkspaceMember(workspace_id={self.workspace_id}, user_id={self.user_id}, role='{self.role.value}')>"
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': str(self.id),
            'workspace_id': str(self.workspace_id),
            'user_id': str(self.user_id),
            'role': self.role.value,
            'invited_by': str(self.invited_by) if self.invited_by else None,
            'invited_at': self.invited_at.isoformat() if self.invited_at else None,
            'joined_at': self.joined_at.isoformat() if self.joined_at else None,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class WorkspaceInvitation(Base):
    """
    Workspace invitation model for tracking pending invitations
    """
    
    __tablename__ = "workspace_invitations"
    
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
    
    # Invitee information
    email = Column(String(255), nullable=False, index=True)
    
    # Invitation details
    role = Column(
        SQLEnum(
            WorkspaceRole,
            name="workspace_role",
            create_type=False,
            native_enum=False,
            values_callable=lambda x: [e.value for e in x]
        ),
        nullable=False,
        default=WorkspaceRole.VIEWER
    )
    
    # Invitation token for accepting
    token = Column(String(255), unique=True, nullable=False, index=True)
    
    # Status
    status = Column(
        SQLEnum(
            InvitationStatus,
            name="invitation_status",
            create_type=False,
            native_enum=False,
            values_callable=lambda x: [e.value for e in x]
        ),
        nullable=False,
        default=InvitationStatus.PENDING,
        index=True
    )
    
    # Who invited
    invited_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # Message to invitee
    message = Column(Text, nullable=True)
    
    # Expiration
    expires_at = Column(DateTime, nullable=False, index=True)
    
    # Response details
    responded_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    workspace = relationship("Workspace")
    inviter = relationship("User", foreign_keys=[invited_by])
    
    def __repr__(self):
        return f"<WorkspaceInvitation(email='{self.email}', workspace_id={self.workspace_id}, status='{self.status.value}')>"
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': str(self.id),
            'workspace_id': str(self.workspace_id),
            'email': self.email,
            'role': self.role.value,
            'status': self.status.value,
            'invited_by': str(self.invited_by) if self.invited_by else None,
            'message': self.message,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'responded_at': self.responded_at.isoformat() if self.responded_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }