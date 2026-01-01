# backend/app/models/workspace.py
"""
Workspace Database Model - COMPLETE WITH SOFT DELETE
Path: backend/app/models/workspace.py
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
import enum

from app.db.base import Base


class WorkspaceType(str, enum.Enum):
    """Workspace type enumeration - must match database ENUM"""
    PERSONAL = "personal"
    TEAM = "team"
    COMMON = "common"


class Workspace(Base):
    """
    Workspace model for organizing models and diagrams
    
    Supports soft delete via deleted_at column
    """
    
    __tablename__ = "workspaces"
    
    # Primary key - UUID to match database schema
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    
    # Workspace identity
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Workspace type using proper enum handling
    type = Column(
        SQLEnum(
            WorkspaceType,
            name="workspace_type",
            create_type=False,
            native_enum=False,  # Use enum values, not names
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
    
    # Additional fields from database schema
    settings = Column(JSONB, nullable=False, default=dict)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # CRITICAL FIX: Add soft delete support
    deleted_at = Column(DateTime, nullable=True, index=True)
    
    # Relationships
    owner = relationship("User", foreign_keys=[created_by], backref="owned_workspaces")
    
    def __repr__(self):
        return f"<Workspace(id={self.id}, name='{self.name}', type='{self.type.value}')>"
    
    @property
    def is_deleted(self):
        """Check if workspace has been soft-deleted"""
        return self.deleted_at is not None
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': str(self.id),
            'name': self.name,
            'description': self.description,
            'type': self.type.value if isinstance(self.type, WorkspaceType) else self.type,
            'created_by': str(self.created_by),
            'settings': self.settings,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'deleted_at': self.deleted_at.isoformat() if self.deleted_at else None,
        }