# backend/app/models/model.py

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
    model_type = Column(String(100), nullable=True)
    
    # Model metadata
    metadata_dict = Column("metadata", JSON, nullable=False, default=lambda: {})
    
    # Ownership
    workspace_id = Column(String(36), nullable=True, index=True)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    updated_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=True, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    
    # Relationships
    diagrams = relationship("Diagram", back_populates="model", cascade="all, delete-orphan")
    creator = relationship("User", foreign_keys=[created_by])
    
    def __repr__(self):
        return f"<Model(id={self.id}, name='{self.name}')>"