# backend/app/models/layout.py
"""
Layout Database Model
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, Boolean, Text
import uuid

from app.db.base import Base


class Layout(Base):
    """Layout model for storing diagram layout configurations"""
    
    __tablename__ = "layouts"
    
    # Primary Key
    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    
    # Basic Info
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Relationships
    diagram_id = Column(String(36), ForeignKey("diagrams.id"), nullable=False, index=True)
    
    # Layout Configuration
    algorithm = Column(String(50), nullable=False, default="manual", index=True)
    # algorithm options: manual, layered, force_directed, bpmn_swimlane, uml_sequence, state_machine
    
    # Layout Data (stored as JSON) - Use lambda to return new instances
    layout_data = Column(JSON, nullable=False, default=lambda: {
        "nodes": [],
        "direction": "TB",
        "spacing": {"node": [80, 80], "rank": 80}
    })
    
    # Settings specific to the layout algorithm
    settings = Column(JSON, nullable=True, default=lambda: {})
    
    # Constraints (pinned nodes, locked sections, etc.)
    constraints = Column(JSON, nullable=True, default=lambda: {})
    
    # Status
    is_default = Column(Boolean, nullable=False, default=False, index=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    
    # Audit Fields
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        index=True,
    )
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    updated_by = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    
    # Soft Delete
    deleted_at = Column(DateTime, nullable=True, index=True)
    
    def __repr__(self):
        return f"<Layout(id={self.id}, name={self.name}, algorithm={self.algorithm})>"