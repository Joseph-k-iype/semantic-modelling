# backend/app/models/diagram.py
"""
Diagram Database Model - FIXED with layouts relationship
Path: backend/app/models/diagram.py
"""
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
import uuid

from app.db.base import Base


class Diagram(Base):
    """
    Diagram model - visual projection of semantic model
    
    Each diagram gets its own FalkorDB graph (one-to-one mapping)
    Format: {workspace_name}/{diagram_name}/{username}
    """
    
    __tablename__ = "diagrams"
    
    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    
    # Foreign keys
    model_id = Column(
        UUID(as_uuid=True),
        ForeignKey("models.id", ondelete="CASCADE"),
        nullable=True,  # Can be NULL for standalone diagrams
        index=True
    )
    
    # Basic information
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Workspace reference (denormalized for easier queries)
    workspace_name = Column(String(255), nullable=True, index=True)
    
    # Notation - always UML_CLASS for Semantic Architect
    notation = Column(String(50), nullable=False, default='UML_CLASS', index=True)
    
    # FalkorDB graph reference
    # Format: {workspace_name}/{diagram_name}/{username}
    graph_name = Column(String(500), unique=True, nullable=True, index=True)
    
    # Publishing
    is_published = Column(Boolean, default=False, nullable=False, index=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    
    # Diagram content and configuration
    notation_config = Column(JSONB, nullable=False, default=dict, server_default='{}')
    
    # Visual settings
    settings = Column(JSONB, nullable=False, default=dict, server_default='{}')
    
    # Flags
    is_default = Column(Boolean, default=False, nullable=False)
    is_valid = Column(Boolean, default=True, nullable=False)
    
    # Validation
    validation_errors = Column(JSONB, nullable=False, default=list, server_default='[]')
    last_validated_at = Column(DateTime(timezone=True), nullable=True)
    
    # Soft delete
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Audit trail
    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False
    )
    updated_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True
    )
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    # CRITICAL FIX: Added layouts relationship with back_populates
    model = relationship("Model", back_populates="diagrams")
    layouts = relationship("Layout", back_populates="diagram", cascade="all, delete-orphan")
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    
    def __repr__(self):
        return f"<Diagram(id={self.id}, name='{self.name}', notation='{self.notation}')>"
    
    @property
    def is_deleted(self):
        """Check if diagram has been soft-deleted"""
        return self.deleted_at is not None
    
    @property
    def node_count(self):
        """Get the number of nodes in this diagram"""
        settings = self.settings or {}
        nodes = settings.get('nodes', [])
        return len(nodes)
    
    @property
    def edge_count(self):
        """Get the number of edges in this diagram"""
        settings = self.settings or {}
        edges = settings.get('edges', [])
        return len(edges)
    
    @property
    def layout_count(self):
        """Get the number of layouts for this diagram"""
        return len(self.layouts) if self.layouts else 0
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': str(self.id),
            'model_id': str(self.model_id) if self.model_id else None,
            'name': self.name,
            'description': self.description,
            'workspace_name': self.workspace_name,
            'notation': self.notation,
            'graph_name': self.graph_name,
            'is_published': self.is_published,
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'notation_config': self.notation_config,
            'settings': self.settings,
            'is_default': self.is_default,
            'is_valid': self.is_valid,
            'validation_errors': self.validation_errors,
            'last_validated_at': self.last_validated_at.isoformat() if self.last_validated_at else None,
            'created_by': str(self.created_by),
            'updated_by': str(self.updated_by) if self.updated_by else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }