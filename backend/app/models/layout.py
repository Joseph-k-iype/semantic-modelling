# backend/app/models/layout.py
"""
Layout Database Model - FIXED
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, JSON, Boolean
import uuid

from app.db.base import Base


class Layout(Base):
    """Layout model for storing diagram layout configurations"""
    
    __tablename__ = "layouts"
    
    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    
    # Layout info
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Relationships
    diagram_id = Column(String(36), ForeignKey("diagrams.id"), nullable=False, index=True)
    
    # Layout algorithm
    algorithm = Column(String(50), nullable=False, index=True)  # manual, layered, force-directed, etc.
    
    # Layout configuration and node positions
    config = Column(JSON, nullable=False, default=lambda: {})
    positions = Column(JSON, nullable=False, default=lambda: {})
    
    # Is this the active layout? - FIXED: Changed from String to Boolean
    is_active = Column(Boolean, nullable=False, default=False)
    
    # Audit
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    updated_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    
    def __repr__(self):
        return f"<Layout(id={self.id}, name={self.name}, algorithm={self.algorithm})>"