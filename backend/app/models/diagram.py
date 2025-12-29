# backend/app/models/diagram.py

from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.db.base import Base


class Diagram(Base):
    """Diagram model - visual projections of semantic models"""
    
    __tablename__ = "diagrams"
    
    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    
    # Parent model
    model_id = Column(String(36), ForeignKey("models.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Diagram identity
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Notation type (er, uml_class, bpmn, etc.)
    notation_type = Column(String(100), nullable=False, index=True)
    
    # Diagram data stored as JSON
    # Contains: nodes, edges, viewport, etc.
    metadata_dict = Column("metadata", JSON, nullable=False, default=lambda: {"nodes": [], "edges": []})
    
    # Ownership
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    updated_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=True, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    
    # Relationships
    model = relationship("Model", back_populates="diagrams")
    creator = relationship("User", foreign_keys=[created_by])
    
    def __repr__(self):
        return f"<Diagram(id={self.id}, name='{self.name}', notation='{self.notation_type}')>"