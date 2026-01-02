# backend/app/models/workspace.py
"""
Workspace Database Models - VERIFIED AND COMPLETE
Path: backend/app/models/workspace.py

CRITICAL: This model uses 'type' (NOT 'workspace_type') for the workspace type column
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
    PERSONAL = "personal"
    TEAM = "team"
    COMMON = "common"


class WorkspaceRole(str, enum.Enum):
    """Workspace member role enumeration - MUST match database ENUM 'user_role'"""
    VIEWER = "viewer"
    EDITOR = "editor"
    PUBLISHER = "publisher"
    ADMIN = "admin"


class InvitationStatus(str, enum.Enum):
    """Invitation status enumeration - MUST match database ENUM 'invitation_status'"""
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"


class Workspace(Base):
    """
    Workspace model for organizing models and collaboration
    
    CRITICAL: Column name is 'type' (NOT 'workspace_type')
    
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
    
    # CRITICAL: Column name is 'type' (NOT 'workspace_type')
    type = Column(
        SQLEnum(
            WorkspaceType,
            name="workspace_type",  # Database ENUM type name
            create_type=False,
            native_enum=False,
            values_callable=lambda x: [e.value for e in x]
        ),
        nullable=False,
        default=WorkspaceType.PERSONAL,
        index=True
    )
    
    # Ownership
    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    
    updated_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    
    deleted_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Customization
    icon = Column(String(50), nullable=True)
    color = Column(String(7), nullable=True)  # Hex color
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_archived = Column(Boolean, default=False, nullable=False, index=True)
    
    # Settings and metadata
    settings = Column(JSONB, default={}, nullable=False)
    meta_data = Column(JSONB, default={}, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True, index=True)
    
    # Relationships
    creator = relationship(
        "User",
        foreign_keys=[created_by],
        back_populates="created_workspaces"
    )
    
    updater = relationship(
        "User",
        foreign_keys=[updated_by]
    )
    
    deleter = relationship(
        "User",
        foreign_keys=[deleted_by]
    )
    
    # Members
    members = relationship(
        "WorkspaceMember",
        back_populates="workspace",
        cascade="all, delete-orphan"
    )
    
    # Models
    models = relationship(
        "Model",
        back_populates="workspace",
        cascade="all, delete-orphan"
    )
    
    # Folders
    folders = relationship(
        "Folder",
        back_populates="workspace",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<Workspace(id={self.id}, name='{self.name}', type='{self.type.value}')>"
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': str(self.id),
            'name': self.name,
            'slug': self.slug,
            'description': self.description,
            'type': self.type.value,  # CRITICAL: Use 'type'
            'created_by': str(self.created_by),
            'updated_by': str(self.updated_by) if self.updated_by else None,
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
            name="user_role",
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
    
    # Relationships
    workspace = relationship("Workspace", back_populates="members")
    user = relationship("User", foreign_keys=[user_id])
    inviter = relationship("User", foreign_keys=[invited_by])
    
    # Unique constraint
    __table_args__ = (
        UniqueConstraint('workspace_id', 'user_id', name='uq_workspace_member'),
    )
    
    def __repr__(self):
        return f"<WorkspaceMember(workspace_id={self.workspace_id}, user_id={self.user_id}, role={self.role.value})>"


class WorkspaceInvitation(Base):
    """
    Workspace invitation model for pending member invitations
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
    
    invited_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Invitee information
    email = Column(String(255), nullable=False, index=True)
    
    # Role to assign
    role = Column(
        SQLEnum(
            WorkspaceRole,
            name="user_role",
            create_type=False,
            native_enum=False,
            values_callable=lambda x: [e.value for e in x]
        ),
        nullable=False,
        default=WorkspaceRole.VIEWER
    )
    
    # Invitation details
    token = Column(String(255), unique=True, nullable=False, index=True)
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
    
    message = Column(Text, nullable=True)
    
    # Timestamps
    expires_at = Column(DateTime, nullable=False, index=True)
    accepted_at = Column(DateTime, nullable=True)
    rejected_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    workspace = relationship("Workspace")
    inviter = relationship("User", foreign_keys=[invited_by])
    
    def __repr__(self):
        return f"<WorkspaceInvitation(email={self.email}, workspace_id={self.workspace_id}, status={self.status.value})>"