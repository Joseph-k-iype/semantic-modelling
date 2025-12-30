# backend/app/models/model.py
"""
Model Database Model - Complete and Fixed
Path: backend/app/models/model.py
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
import uuid

from app.db.base import Base


class Model(Base):
    """Model model - semantic models containing business logic"""
    
    __tablename__ = "models"
    
    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    
    # Model identity
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Model type/category
    model_type = Column(String(100), nullable=False, index=True)
    # Supported types: er, uml, bpmn, semantic, custom
    
    # Model status
    status = Column(String(50), nullable=False, default="draft", index=True)
    # Status values: draft, published, archived
    
    # Model data stored as JSON
    # This is the semantic model data - notation-agnostic
    data = Column(JSON, nullable=False, default=lambda: {})
    
    # Model metadata (tags, categories, etc.)
    meta_data = Column('metadata', JSON, nullable=False, default=lambda: {})
    
    # Ownership and organization
    workspace_id = Column(
        String(36),
        ForeignKey("workspaces.id"),
        nullable=False,
        index=True
    )
    folder_id = Column(
        String(36),
        ForeignKey("folders.id"),
        nullable=True,
        index=True
    )
    
    # Ownership - FIXED: now String(36) to match User model
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    updated_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=True, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)  # Soft delete
    
    # Published version tracking
    published_version = Column(String(36), nullable=True)
    published_at = Column(DateTime, nullable=True)
    
    # Relationships
    workspace = relationship("Workspace", backref="models")
    folder = relationship("Folder", backref="models")
    diagrams = relationship(
        "Diagram",
        back_populates="model",
        cascade="all, delete-orphan"
    )
    creator = relationship(
        "User",
        foreign_keys=[created_by],
        backref="created_models"
    )
    updater = relationship(
        "User",
        foreign_keys=[updated_by]
    )
    
    def __repr__(self):
        return f"<Model(id={self.id}, name='{self.name}', type='{self.model_type}', status='{self.status}')>"
    
    @property
    def is_published(self):
        """Check if model is published"""
        return self.status == "published"
    
    @property
    def is_draft(self):
        """Check if model is in draft status"""
        return self.status == "draft"
    
    @property
    def is_archived(self):
        """Check if model is archived"""
        return self.status == "archived"
    
    @property
    def is_deleted(self):
        """Check if model has been soft-deleted"""
        return self.deleted_at is not None
    
    @property
    def diagram_count(self):
        """Get the number of diagrams for this model"""
        return len(self.diagrams) if hasattr(self, 'diagrams') else 0