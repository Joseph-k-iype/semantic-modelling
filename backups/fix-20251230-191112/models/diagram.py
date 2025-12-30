# backend/app/models/diagram.py
"""
Diagram Database Model - COMPLETE AND FIXED
Path: backend/app/models/diagram.py
"""
from datetime import datetime
from sqlalchemy import Column, String, Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

from app.db.base import Base


class Diagram(Base):
    """Diagram model - visual projections of semantic models"""
    
    __tablename__ = "diagrams"
    
    # Primary key - use UUID for better distribution and security
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    
    # Parent model - diagrams are projections of models
    model_id = Column(
        UUID(as_uuid=True),
        ForeignKey("models.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Diagram identity
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Notation type - defines what visual language is used
    notation_type = Column(String(100), nullable=False, index=True)
    # Supported types: er, uml_class, uml_sequence, uml_activity, uml_state,
    # uml_component, uml_deployment, bpmn, graph, custom
    
    # Diagram data stored as JSON
    # Contains: nodes, edges, viewport settings, notation-specific config
    data = Column(
        JSONB,
        nullable=False,
        default=lambda: {
            "nodes": [],
            "edges": [],
            "viewport": {
                "x": 0,
                "y": 0,
                "zoom": 1.0
            }
        }
    )
    
    # Diagram metadata (validation results, statistics, etc.)
    # Using column name 'meta_data' to avoid conflict with SQLAlchemy's metadata
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
    model = relationship("Model", back_populates="diagrams")
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