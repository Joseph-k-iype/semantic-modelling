# backend/app/models/layout.py
"""
Layout Database Model - COMPLETE AND FIXED
Path: backend/app/models/layout.py
"""
from datetime import datetime
from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

from app.db.base import Base


class Layout(Base):
    """Layout model for storing diagram layout configurations"""
    
    __tablename__ = "layouts"
    
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
    
    # Layout configuration
    layout_engine = Column(String(100), nullable=False, index=True)
    # Supported engines: manual, layered, force_directed, bpmn_swimlane, 
    # uml_sequence, state_machine, hierarchical
    
    # Layout data stored as JSONB
    # Contains: node positions, edge routes, constraints, etc.
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
        }
    )
    
    # Settings
    is_default = Column(Boolean, default=False, nullable=False)
    is_locked = Column(Boolean, default=False, nullable=False)
    
    # Ownership
    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    updated_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
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
    
    # Relationships
    diagram = relationship("Diagram", backref="layouts")
    creator = relationship(
        "User",
        foreign_keys=[created_by],
        backref="created_layouts"
    )
    updater = relationship(
        "User",
        foreign_keys=[updated_by]
    )
    
    def __repr__(self):
        return f"<Layout(id={self.id}, name='{self.name}', engine='{self.layout_engine}', default={self.is_default})>"
    
    @property
    def node_count(self):
        """Get the number of nodes in this layout"""
        return len(self.layout_data.get("nodes", {}))
    
    @property
    def edge_count(self):
        """Get the number of edges in this layout"""
        return len(self.layout_data.get("edges", {}))