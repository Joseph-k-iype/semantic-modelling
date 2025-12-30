# backend/app/models/folder.py
"""
Folder Database Model - FIXED with UUID types
Path: backend/app/models/folder.py
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.db.base import Base


class Folder(Base):
    """Folder model for organizing models within workspaces"""
    
    __tablename__ = "folders"
    
    # Primary key - FIXED: UUID type
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    
    # Folder identity
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Hierarchy - folders can be nested
    # FIXED: UUID types for foreign keys
    parent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("folders.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    
    workspace_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Display order for sorting
    sort_order = Column(Integer, nullable=False, default=0)
    
    # Ownership - FIXED: UUID types
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
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)  # Soft delete
    
    # Relationships
    parent = relationship(
        "Folder",
        remote_side=[id],
        backref="children",
        foreign_keys=[parent_id]
    )
    workspace = relationship("Workspace", backref="folders")
    creator = relationship("User", foreign_keys=[created_by], backref="created_folders")
    updater = relationship("User", foreign_keys=[updated_by])
    
    def __repr__(self):
        return f"<Folder(id={self.id}, name='{self.name}', workspace_id='{self.workspace_id}')>"
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': str(self.id),
            'name': self.name,
            'description': self.description,
            'workspace_id': str(self.workspace_id),
            'parent_id': str(self.parent_id) if self.parent_id else None,
            'sort_order': self.sort_order,
            'created_by': str(self.created_by),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @property
    def full_path(self):
        """Get the full path of this folder"""
        if self.parent:
            return f"{self.parent.full_path}/{self.name}"
        return self.name
    
    @property
    def depth(self):
        """Get the depth level of this folder (0 for root folders)"""
        if self.parent:
            return self.parent.depth + 1
        return 0
    
    @property
    def is_deleted(self):
        """Check if folder has been soft-deleted"""
        return self.deleted_at is not None