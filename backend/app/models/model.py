"""
Model Database Model
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, JSON
import uuid

from app.db.base import Base


class Model(Base):
    """Model - represents a logical model that can have multiple diagrams"""
    
    __tablename__ = "models"
    
    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    type = Column(String(50), nullable=False)  # ER, UML, BPMN
    
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False, index=True)
    folder_id = Column(String(36), ForeignKey("folders.id"), nullable=True, index=True)
    
    # Model metadata
    meta_data = Column('metadata', JSON, nullable=True, default=lambda: {})
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    updated_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    
    def __repr__(self):
        return f"<Model(id={self.id}, name={self.name})>"