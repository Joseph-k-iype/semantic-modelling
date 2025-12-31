# backend/app/models/workspace.py
"""
Workspace Database Model - FIXED with correct relationships
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
    
    CRITICAL FIX: Using SQLAlchemy Enum type to match PostgreSQL workspace_type ENUM
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
    
    # CRITICAL FIX: Using SQLAlchemy Enum type for PostgreSQL ENUM
    # This properly casts to the workspace_type ENUM in database
    type = Column(
        SQLEnum(WorkspaceType, name="workspace_type", create_type=False),
        nullable=False,
        default=WorkspaceType.PERSONAL,
        index=True
    )
    
    # FIXED: Column name is 'created_by' in database
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
    
    # Relationships - CRITICAL FIX: Use backref instead of back_populates
    # This creates the relationship on User automatically without needing to define it there
    owner = relationship("User", foreign_keys=[created_by], backref="owned_workspaces")
    
    # Other relationships use backref to avoid circular imports
    # models = relationship("Model", backref="workspace", cascade="all, delete-orphan")
    # folders = relationship("Folder", backref="workspace", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Workspace(id={self.id}, name='{self.name}', type='{self.type.value}')>"
    
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
        }