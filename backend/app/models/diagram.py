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
    
    # Visible concepts from semantic model (as UUIDs)
    visible_concepts = Column(
        ARRAY(UUID(as_uuid=True)),
        nullable=False,
        default=list,
        server_default='{}'
    )
    
    # Additional settings
    settings = Column(
        JSONB,
        nullable=False,
        default=dict,
        server_default='{}'
    )
    
    # Soft delete support
    deleted_at = Column(
        DateTime(timezone=True),
        nullable=True,
        index=True
    )
    
    # Ownership and audit fields
    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    
    updated_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True
    )
    
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        index=True
    )
    
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    
    # Relationships
    model = relationship(
        "Model",
        back_populates="diagrams",
        lazy="select"
    )
    
    layouts = relationship(
        "Layout",
        back_populates="diagram",
        cascade="all, delete-orphan",
        lazy="select",
        order_by="Layout.is_default.desc(), Layout.created_at.desc()"
    )
    
    creator = relationship(
        "User",
        foreign_keys=[created_by],
        lazy="select"
    )
    
    updater = relationship(
        "User",
        foreign_keys=[updated_by],
        lazy="select"
    )
    
    def __repr__(self) -> str:
        return f"<Diagram(id={self.id}, name='{self.name}', notation='{self.notation}', model_id={self.model_id})>"
    
    def to_dict(self) -> dict:
        """Convert diagram to dictionary"""
        return {
            "id": str(self.id),
            "model_id": str(self.model_id),
            "name": self.name,
            "description": self.description,
            "notation": self.notation,
            "notation_config": self.notation_config,
            "visible_concepts": [str(c) for c in (self.visible_concepts or [])],
            "settings": self.settings,
            "created_by": str(self.created_by),
            "updated_by": str(self.updated_by) if self.updated_by else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None
        }