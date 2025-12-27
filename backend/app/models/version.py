"""
Version Database Model
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, JSON, Integer
import uuid

from app.db.base import Base


class Version(Base):
    """Version model for tracking model/diagram versions"""
    
    __tablename__ = "versions"
    
    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    
    # Versioned entity
    entity_type = Column(String(50), nullable=False, index=True)  # model, diagram
    entity_id = Column(String(36), nullable=False, index=True)
    
    # Version info
    version_number = Column(Integer, nullable=False)
    name = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    
    # Snapshot data
    snapshot_data = Column(JSON, nullable=False, default=lambda: {})
    
    # Audit
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    
    def __repr__(self):
        return f"<Version(id={self.id}, entity={self.entity_type}, version={self.version_number})>"