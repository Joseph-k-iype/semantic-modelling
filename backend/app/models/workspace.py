# backend/app/models/workspace.py
"""
Workspace Database Model - FIXED to match actual database schema
Path: backend/app/models/workspace.py
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

from app.db.base import Base


class Workspace(Base):
    """
    Workspace model for organizing models and diagrams
    
    CRITICAL: Column names MUST match database schema in 02-workspaces.sql
    Database has: type, created_by, settings, is_active
    NOT: workspace_type, owner_id
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
    
    # FIXED: Column name is 'type' in database, not 'workspace_type'
    # Using mapped_column to map Python attribute to different database column
    workspace_type = mapped_column("type", String(50), nullable=False, default="personal", index=True)
    # workspace_type options: personal, team, common
    
    # FIXED: Column name is 'created_by' in database, not 'owner_id'
    # Using mapped_column to map Python attribute to different database column
    owner_id = mapped_column(
        "created_by",
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
    
    # Relationships
    owner = relationship("User", foreign_keys=[owner_id], backref="owned_workspaces")
    
    def __repr__(self):
        return f"<Workspace(id={self.id}, name='{self.name}', type='{self.workspace_type}')>"
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': str(self.id),
            'name': self.name,
            'description': self.description,
            'workspace_type': self.workspace_type,
            'owner_id': str(self.owner_id),
            'settings': self.settings,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }