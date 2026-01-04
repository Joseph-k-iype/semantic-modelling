# backend/app/models/diagram.py
"""
Diagram Database Model - Updated for Semantic Architect
Path: backend/app/models/diagram.py
"""
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
import uuid

from app.db.base import Base


class Diagram(Base):
    """
    Diagram model - visual projection of semantic model
    
    Each diagram gets its own FalkorDB graph (one-to-one mapping)
    Format: {workspace_name}/{diagram_name}/{username}
    """
    
    __tablename__ = "diagrams"
    
    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    
    # Foreign keys
    model_id = Column(
        UUID(as_uuid=True),
        ForeignKey("models.id", ondelete="CASCADE"),
        nullable=True,  # Can be NULL for standalone diagrams
        index=True
    )
    
    # Basic information
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Workspace reference (denormalized for easier queries)
    workspace_name = Column(String(255), nullable=True, index=True)
    
    # Notation - always UML_CLASS for Semantic Architect
    notation = Column(String(50), nullable=False, default='UML_CLASS', index=True)
    
    # FalkorDB graph reference
    # Format: {workspace_name}/{diagram_name}/{username}
    graph_name = Column(String(500), unique=True, nullable=True, index=True)
    
    # Publishing
    is_published = Column(Boolean, default=False, nullable=False, index=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    
    # Diagram content and configuration
    notation_config = Column(JSONB, nullable=False, default=dict, server_default='{}')
    
    # Visual settings
    settings = Column(JSONB, nullable=False, default=dict, server_default='{}')
    
    # Flags
    is_default = Column(Boolean, default=False, nullable=False)
    is_valid = Column(Boolean, default=True, nullable=False)
    
    # Validation
    validation_errors = Column(JSONB, nullable=False, default=list, server_default='[]')
    last_validated_at = Column(DateTime(timezone=True), nullable=True)
    
    # Soft delete
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Audit trail
    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False
    )
    updated_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True
    )
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    model = relationship("Model", back_populates="diagrams")
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])