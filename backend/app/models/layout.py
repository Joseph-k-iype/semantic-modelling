# backend/app/models/layout.py
"""
Layout Database Model - COMPLETE matching updated schema
Path: backend/app/models/layout.py
"""
from datetime import datetime
from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

from app.db.base import Base


class Layout(Base):
    """
    Layout model for storing diagram layout configurations
    User-controlled layouts for different diagram views
    """
    
    __tablename__ = "layouts"
    
    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    
    # Parent diagram
    diagram_id = Column(
        UUID(as_uuid=True),
        ForeignKey("diagrams.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Layout identity
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Layout engine type
    # Supported engines: manual, layered, force_directed, bpmn_swimlane, 
    # uml_sequence, state_machine, hierarchical
    layout_engine = Column(
        String(100), 
        nullable=False, 
        index=True, 
        default='manual',
        name='engine'  # Database column name
    )
    
    # Engine-specific configuration
    engine_config = Column(
        JSONB,
        nullable=False,
        default=dict,
        server_default='{}'
    )
    
    # Layout data stored as JSONB
    # Contains: node positions, edge routes, constraints, viewport, etc.
    layout_data = Column(
        JSONB,
        nullable=False,
        default=lambda: {
            "nodes": {},      # Node positions: {node_id: {x, y, width, height}}
            "edges": {},      # Edge routes: {edge_id: {points: [{x, y}]}}
            "constraints": {}, # Layout constraints
            "viewport": {     # Viewport settings
                "x": 0,
                "y": 0,
                "zoom": 1.0
            }
        },
        name='positions'  # Database column name (legacy)
    )
    
    # Layout constraints (pinned nodes, locked sections, etc.)
    constraints = Column(
        JSONB,
        nullable=False,
        default=dict,
        server_default='{}'
    )
    
    # Is this the default layout for the diagram?
    is_default = Column(
        Boolean,
        nullable=False,
        default=False,
        index=True
    )
    
    # Soft delete support
    deleted_at = Column(
        DateTime(timezone=True),
        nullable=True,
        index=True
    )
    
    # Ownership and audit fields
    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        index=True
    )
    
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    
    # Relationships
    diagram = relationship(
        "Diagram",
        back_populates="layouts",
        lazy="select"
    )
    
    creator = relationship(
        "User",
        foreign_keys=[created_by],
        lazy="select"
    )
    
    def __repr__(self) -> str:
        return f"<Layout(id={self.id}, name='{self.name}', diagram_id={self.diagram_id}, engine='{self.layout_engine}', is_default={self.is_default})>"
    
    def to_dict(self) -> dict:
        """Convert layout to dictionary"""
        return {
            "id": str(self.id),
            "diagram_id": str(self.diagram_id),
            "name": self.name,
            "description": self.description,
            "engine": self.layout_engine,
            "engine_config": self.engine_config,
            "layout_data": self.layout_data,
            "constraints": self.constraints,
            "is_default": self.is_default,
            "created_by": str(self.created_by),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None
        }