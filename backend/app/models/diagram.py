# backend/app/models/diagram.py
"""
Diagram Database Model - COMPLETE AND PRODUCTION READY
Matches database schema: database/postgres/schema/05-diagrams.sql
Path: backend/app/models/diagram.py
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
import uuid

from app.db.base import Base


class Diagram(Base):
    """
    Diagram model - visual projections of semantic models
    
    Database schema mapping:
    - notation (NOT notation_type)
    - notation_config (NOT data)
    - visible_concepts (UUID array)
    - settings (JSONB)
    """
    
    __tablename__ = "diagrams"
    
    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    
    # Parent model relationship
    model_id = Column(
        UUID(as_uuid=True),
        ForeignKey("models.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Diagram identity
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Notation type - MATCHES DATABASE: 'notation' not 'notation_type'
    notation = Column(String(100), nullable=False, index=True)
    
    # Notation configuration - MATCHES DATABASE
    notation_config = Column(
        JSONB,
        nullable=False,
        default=dict,
        server_default='{}'
    )
    
    # Which concepts from the model are visible in this diagram
    visible_concepts = Column(
        ARRAY(UUID(as_uuid=True)),
        nullable=False,
        default=list,
        server_default='{}'
    )
    
    # Diagram-specific settings
    settings = Column(
        JSONB,
        nullable=False,
        default=dict,
        server_default='{}'
    )
    
    # Ownership
    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
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
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        index=True
    )
    
    # Relationships - ✅ FIXED: Use back_populates to match Model.diagrams
    model = relationship("Model", back_populates="diagrams")
    creator = relationship("User", foreign_keys=[created_by], backref="created_diagrams")
    updater = relationship("User", foreign_keys=[updated_by])
    
    def __repr__(self):
        return f"<Diagram(id={self.id}, name='{self.name}', notation='{self.notation}')>"
    
    def to_dict(self):
        """Convert diagram to dictionary"""
        return {
            'id': str(self.id),
            'model_id': str(self.model_id),
            'name': self.name,
            'description': self.description,
            'notation': self.notation,
            'notation_config': self.notation_config or {},
            'visible_concepts': [str(c) for c in (self.visible_concepts or [])],
            'settings': self.settings or {},
            'created_by': str(self.created_by),
            'updated_by': str(self.updated_by) if self.updated_by else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @property
    def concept_count(self):
        """Get the number of visible concepts"""
        return len(self.visible_concepts) if self.visible_concepts else 0
    
    @property
    def is_uml(self):
        """Check if this is a UML diagram"""
        return self.notation.startswith("uml_")
    
    @property
    def is_bpmn(self):
        """Check if this is a BPMN diagram"""
        return self.notation == "bpmn"
    
    @property
    def is_er(self):
        """Check if this is an ER diagram"""
        return self.notation == "er"
    
    @property
    def notation_type(self):
        """Compatibility property - frontend may still use notation_type"""
        return self.notation
    
    @notation_type.setter
    def notation_type(self, value):
        """Compatibility setter - frontend may still set notation_type"""
        self.notation = value