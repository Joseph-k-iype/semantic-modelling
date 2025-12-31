# backend/app/models/folder.py
"""
Folder Database Model - COMPLETE matching database schema
Path: backend/app/models/folder.py
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.db.base import Base


class Folder(Base):
    """
    Folder model for organizing models within workspaces
    
    CRITICAL: Column names MUST match database schema in 03-folders.sql
    Database columns: workspace_id, parent_id, position, path, color, icon, created_by
    """
    
    __tablename__ = "folders"
    
    # Primary key - UUID type
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    
    # Relationships to workspace and parent folder
    workspace_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    parent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("folders.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    
    # Folder identity
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Visual attributes (from database schema)
    color = Column(String(50), nullable=True)
    icon = Column(String(100), nullable=True)
    
    # Materialized path for efficient queries
    path = Column(Text, nullable=False, default='')
    
    # Display order for sorting (called 'position' in database)
    position = Column(Integer, nullable=False, default=0)
    
    # Ownership - UUID type
    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    parent = relationship(
        "Folder",
        remote_side=[id],
        backref="children",
        foreign_keys=[parent_id]
    )
    workspace = relationship("Workspace", backref="folders")
    creator = relationship("User", foreign_keys=[created_by], backref="created_folders")
    # models relationship is defined in Model model via backref
    
    def __repr__(self):
        return f"<Folder(id={self.id}, name='{self.name}', workspace_id='{self.workspace_id}')>"
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': str(self.id),
            'workspace_id': str(self.workspace_id),
            'parent_id': str(self.parent_id) if self.parent_id else None,
            'name': self.name,
            'description': self.description,
            'color': self.color,
            'icon': self.icon,
            'path': self.path,
            'position': self.position,
            'created_by': str(self.created_by),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @property
    def depth(self):
        """Get folder depth based on path"""
        return len(self.path.split('/')) - 1 if self.path else 0
    
    @property
    def has_children(self):
        """Check if folder has subfolders"""
        return len(self.children) > 0 if hasattr(self, 'children') else False