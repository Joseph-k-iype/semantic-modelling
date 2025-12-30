# backend/app/models/workspace.py
"""
Workspace Database Model - FIXED with UUID foreign keys
Path: backend/app/models/workspace.py
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.db.base import Base


class Workspace(Base):
    """Workspace model for organizing models and diagrams"""
    
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
    workspace_type = Column(String(50), nullable=False, default="personal", index=True)
    # workspace_type options: personal, team, common
    
    # Ownership - FIXED: UUID type to match User model
    owner_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("users.id", ondelete="RESTRICT"), 
        nullable=False, 
        index=True
    )
    
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
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }