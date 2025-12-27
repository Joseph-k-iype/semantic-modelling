"""
Folder Database Model
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
import uuid

from app.db.base import Base


class Folder(Base):
    """Folder model for organizing models"""
    
    __tablename__ = "folders"
    
    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False, index=True)
    parent_folder_id = Column(String(36), ForeignKey("folders.id"), nullable=True, index=True)
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    
    def __repr__(self):
        return f"<Folder(id={self.id}, name={self.name})>"
