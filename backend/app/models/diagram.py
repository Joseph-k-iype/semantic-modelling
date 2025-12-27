"""
Diagram Database Model
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, Text
import uuid

from app.db.base import Base


class Diagram(Base):
    """Diagram model for storing diagram data"""
    
    __tablename__ = "diagrams"
    
    # Primary Key
    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    
    # Basic Info
    name = Column(String(255), nullable=False, index=True)
    type = Column(String(50), nullable=False, index=True)  # ER, UML_CLASS, BPMN, etc.
    description = Column(Text, nullable=True)
    
    # Relationships
    model_id = Column(String(36), ForeignKey("models.id"), nullable=True, index=True)
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False, index=True)
    folder_id = Column(String(36), ForeignKey("folders.id"), nullable=True, index=True)
    
    # Diagram Data (stored as JSON) - Use lambda to return new instances
    nodes = Column(JSON, nullable=False, default=lambda: [])
    edges = Column(JSON, nullable=False, default=lambda: [])
    viewport = Column(JSON, nullable=False, default=lambda: {"x": 0, "y": 0, "zoom": 1})
    
    # Metadata - RENAMED from 'metadata' to 'meta_data' (metadata is reserved by SQLAlchemy)
    meta_data = Column('metadata', JSON, nullable=True, default=lambda: {})
    
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
    updated_by = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    
    # Soft Delete
    deleted_at = Column(DateTime, nullable=True, index=True)
    
    def __repr__(self):
        return f"<Diagram(id={self.id}, name={self.name}, type={self.type})>"