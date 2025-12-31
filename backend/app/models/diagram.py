# backend/app/models/diagram.py
"""
Diagram Database Model - COMPLETE with all properties and methods
Path: backend/app/models/diagram.py
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

from app.db.base import Base


class Diagram(Base):
    """
    Diagram model representing visual projections of semantic models
    Multiple diagrams can represent the same model with different notations/views
    """
    
    __tablename__ = "diagrams"
    
    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    
    # Parent model relationship
    model_id = Column(
        UUID(as_uuid=True),
        ForeignKey("models.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Diagram identity
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Notation type - er, uml_class, uml_sequence, bpmn, etc.
    notation_type = Column(String(100), nullable=False, index=True)
    
    # Diagram data - nodes, edges, and other visual elements
    # Using 'data' as column name - no conflict with Python dict
    data = Column(
        JSONB,
        nullable=False,
        default=lambda: {
            "nodes": [],
            "edges": [],
            "viewport": {"x": 0, "y": 0, "zoom": 1}
        }
    )
    
    # Metadata - using column name 'meta_data' to avoid conflict with SQLAlchemy's metadata
    meta_data = Column('metadata', JSONB, nullable=False, default=dict)
    
    # Ownership
    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False
    )
    updated_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True
    )
    
    # Timestamps
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True
    )
    updated_at = Column(
        DateTime,
        nullable=True,
        onupdate=datetime.utcnow
    )
    deleted_at = Column(DateTime, nullable=True)  # Soft delete
    
    # Relationships
    # NOTE: The 'model' relationship is created automatically by the backref 
    # in Model.diagrams relationship, so we don't define it here
    
    creator = relationship(
        "User",
        foreign_keys=[created_by],
        backref="created_diagrams"
    )
    updater = relationship(
        "User",
        foreign_keys=[updated_by]
    )
    # layouts relationship is defined in Layout model via backref
    
    def __repr__(self):
        return f"<Diagram(id={self.id}, name='{self.name}', notation='{self.notation_type}')>"
    
    def to_dict(self):
        """Convert diagram to dictionary"""
        return {
            'id': str(self.id),
            'model_id': str(self.model_id),
            'name': self.name,
            'description': self.description,
            'notation_type': self.notation_type,
            'data': self.data,
            'meta_data': self.meta_data,
            'created_by': str(self.created_by),
            'updated_by': str(self.updated_by) if self.updated_by else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @property
    def is_deleted(self):
        """Check if diagram has been soft-deleted"""
        return self.deleted_at is not None
    
    @property
    def node_count(self):
        """Get the number of nodes in this diagram"""
        return len(self.data.get("nodes", [])) if self.data else 0
    
    @property
    def edge_count(self):
        """Get the number of edges in this diagram"""
        return len(self.data.get("edges", [])) if self.data else 0
    
    @property
    def layout_count(self):
        """Get the number of layouts for this diagram"""
        return len(self.layouts) if hasattr(self, 'layouts') else 0
    
    @property
    def is_uml(self):
        """Check if this is a UML diagram"""
        return self.notation_type.startswith("uml_")
    
    @property
    def is_bpmn(self):
        """Check if this is a BPMN diagram"""
        return self.notation_type == "bpmn"
    
    @property
    def is_er(self):
        """Check if this is an ER diagram"""
        return self.notation_type == "er"