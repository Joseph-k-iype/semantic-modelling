# backend/app/models/folder.py
"""
Folder Database Model - COMPLETE Implementation
Path: backend/app/models/folder.py
"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

from app.db.base import Base


class Folder(Base):
    """
    Folder model for organizing models within workspaces
    Uses materialized path pattern for hierarchical structure
    """
    
    __tablename__ = "folders"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Foreign keys
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("folders.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # Basic information
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Hierarchy information (materialized path)
    path = Column(Text, nullable=False, index=True)  # e.g., "/folder1/subfolder2"
    level = Column(Integer, default=0, nullable=False)  # Depth in hierarchy
    
    # Visual customization
    icon = Column(String(50), nullable=True)
    color = Column(String(7), nullable=True)  # Hex color
    
    # Settings and additional data
    settings = Column(JSONB, default=dict, server_default='{}')
    meta_data = Column(JSONB, default=dict, server_default='{}')
    
    # Timestamps
    deleted_at = Column(DateTime, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Audit trail
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Constraints
    __table_args__ = (
        CheckConstraint("LENGTH(TRIM(name)) >= 1 AND LENGTH(name) <= 255", name="folders_name_check"),
        CheckConstraint("color IS NULL OR color ~* '^#[0-9A-Fa-f]{6}$'", name="folders_color_check"),
        CheckConstraint("level >= 0 AND level < 10", name="folders_level_check"),
        CheckConstraint("LENGTH(path) >= 1", name="folders_path_check"),
        UniqueConstraint('workspace_id', 'parent_id', 'name', 'deleted_at', name='folders_unique_name_per_parent'),
    )
    
    # Relationships
    workspace = relationship("Workspace", back_populates="folders")
    parent = relationship("Folder", remote_side=[id], backref="children")
    models = relationship("Model", back_populates="folder")
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    
    def __repr__(self):
        return f"<Folder(id={self.id}, name='{self.name}', path='{self.path}')>"
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': str(self.id),
            'workspace_id': str(self.workspace_id),
            'parent_id': str(self.parent_id) if self.parent_id else None,
            'name': self.name,
            'description': self.description,
            'path': self.path,
            'level': self.level,
            'icon': self.icon,
            'color': self.color,
            'settings': self.settings,
            'meta_data': self.meta_data,
            'created_by': str(self.created_by),
            'updated_by': str(self.updated_by) if self.updated_by else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }