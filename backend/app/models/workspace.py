# backend/app/models/workspace.py
"""
Workspace Database Model - Complete and Fixed
Path: backend/app/models/workspace.py
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
import uuid

from app.db.base import Base


class Workspace(Base):
    """Workspace model for organizing models and diagrams"""
    
    __tablename__ = "workspaces"
    
    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    
    # Workspace identity
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    workspace_type = Column(String(50), nullable=False, default="personal", index=True)  # personal, team, common
    
    # Ownership - FIXED: now matches User model String(36)
    owner_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    owner = relationship("User", foreign_keys=[owner_id], backref="owned_workspaces")
    
    def __repr__(self):
        return f"<Workspace(id={self.id}, name='{self.name}', type='{self.workspace_type}')>"