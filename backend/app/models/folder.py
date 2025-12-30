# backend/app/models/folder.py
"""
Folder Database Model - Complete and Fixed
Path: backend/app/models/folder.py
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Integer
from sqlalchemy.orm import relationship
import uuid

from app.db.base import Base


class Folder(Base):
    """Folder model for organizing models within workspaces"""
    
    __tablename__ = "folders"
    
    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    
    # Folder identity
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Hierarchy - folders can be nested
    parent_id = Column(String(36), ForeignKey("folders.id"), nullable=True, index=True)
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False, index=True)
    
    # Display order for sorting
    sort_order = Column(Integer, nullable=False, default=0)
    
    # Ownership - FIXED: now String(36) to match User model
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    updated_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=True, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    
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