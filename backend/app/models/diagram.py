# backend/app/models/diagram.py
"""
Diagram Database Model - FULLY FIXED AND COMPLETE
Path: backend/app/models/diagram.py

CRITICAL FIX: Column name is 'notation' (NOT 'notation_type')
This matches the SQL schema in 05-diagrams.sql and uses the diagram_notation ENUM type
"""
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
import uuid
import enum

from app.db.base import Base


class NotationType(str, enum.Enum):
    """Notation type enumeration - matches diagram_notation ENUM in database"""
    ER = "ER"
    UML_CLASS = "UML_CLASS"
    UML_SEQUENCE = "UML_SEQUENCE"
    UML_ACTIVITY = "UML_ACTIVITY"
    UML_STATE = "UML_STATE"
    UML_COMPONENT = "UML_COMPONENT"
    UML_DEPLOYMENT = "UML_DEPLOYMENT"
    UML_PACKAGE = "UML_PACKAGE"
    BPMN = "BPMN"


class Diagram(Base):
    """
    Diagram model - visual projection of semantic model
    
    A diagram represents a specific view/projection of a model using a particular notation.
    The same model can have multiple diagrams (e.g., class diagram, sequence diagram, etc.)
    
    The semantic model itself is stored in FalkorDB (graph database).
    This table stores metadata, notation configuration, and visual settings.
    
    Notation Types:
    - ER: Entity-Relationship diagram
    - UML_CLASS: UML Class diagram
    - UML_SEQUENCE: UML Sequence diagram
    - UML_ACTIVITY: UML Activity diagram
    - UML_STATE: UML State Machine diagram
    - UML_COMPONENT: UML Component diagram
    - UML_DEPLOYMENT: UML Deployment diagram
    - UML_PACKAGE: UML Package diagram
    - BPMN: Business Process Model and Notation
    """
    
    __tablename__ = "diagrams"
    
    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    
    # Foreign key to model
    model_id = Column(
        UUID(as_uuid=True),
        ForeignKey("models.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Basic information
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # CRITICAL FIX: Column name is 'notation' (NOT 'notation_type')
    # This matches the SQL schema and uses the diagram_notation ENUM type
    notation = Column(String(50), nullable=False, index=True)
    
    # Notation-specific configuration (swimlane settings, sequence diagram config, etc.)
    notation_config = Column(JSONB, nullable=False, default=dict, server_default='{}')
    
    # Array of concept UUIDs visible in this diagram (from FalkorDB)
    # Diagrams can show a subset of the model's concepts
    visible_concepts = Column(ARRAY(UUID(as_uuid=True)), nullable=False, default=list, server_default='{}')
    
    # Additional diagram settings (viewport, zoom, grid, style, etc.)
    settings = Column(JSONB, nullable=False, default=dict, server_default='{}')
    
    # Is this the default diagram for the model?
    is_default = Column(Boolean, default=False, nullable=False)
    
    # Validation state
    validation_errors = Column(JSONB, nullable=False, default=list, server_default='[]')
    is_valid = Column(Boolean, default=True, nullable=False)
    last_validated_at = Column(DateTime, nullable=True)
    
    # Soft delete support
    deleted_at = Column(DateTime, nullable=True, index=True)
    
    # Ownership and audit
    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    updated_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
        index=True
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
        onupdate=datetime.utcnow
    )
    
    # Relationships
    model = relationship("Model", back_populates="diagrams")
    layouts = relationship(
        "Layout",
        back_populates="diagram",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    creator = relationship(
        "User",
        foreign_keys=[created_by],
        backref="created_diagrams"
    )
    updater = relationship(
        "User",
        foreign_keys=[updated_by],
        backref="updated_diagrams"
    )
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('model_id', 'name', 'deleted_at', name='uq_diagrams_model_name_not_deleted'),
        CheckConstraint("char_length(trim(name)) >= 1 AND char_length(name) <= 255", name='ck_diagrams_name_length'),
    )
    
    def __repr__(self):
        return f"<Diagram(id={self.id}, name='{self.name}', notation='{self.notation}')>"
    
    @property
    def is_deleted(self):
        """Check if diagram has been soft-deleted"""
        return self.deleted_at is not None
    
    @property
    def concept_count(self):
        """Get the number of visible concepts in this diagram"""
        return len(self.visible_concepts) if self.visible_concepts else 0
    
    @property
    def layout_count(self):
        """Get the number of layouts for this diagram"""
        return len(self.layouts) if self.layouts else 0
    
    @property
    def is_uml(self):
        """Check if this is a UML diagram"""
        return self.notation.startswith("UML_")
    
    @property
    def is_bpmn(self):
        """Check if this is a BPMN diagram"""
        return self.notation == "BPMN"
    
    @property
    def is_er(self):
        """Check if this is an ER diagram"""
        return self.notation == "ER"
    
    @property
    def diagram_type_display(self):
        """Get human-readable diagram type"""
        type_names = {
            "ER": "Entity-Relationship",
            "UML_CLASS": "UML Class Diagram",
            "UML_SEQUENCE": "UML Sequence Diagram",
            "UML_ACTIVITY": "UML Activity Diagram",
            "UML_STATE": "UML State Machine Diagram",
            "UML_COMPONENT": "UML Component Diagram",
            "UML_DEPLOYMENT": "UML Deployment Diagram",
            "UML_PACKAGE": "UML Package Diagram",
            "BPMN": "BPMN Process Diagram",
        }
        return type_names.get(self.notation, self.notation)
    
    def to_dict(self):
        """Convert diagram to dictionary"""
        return {
            'id': str(self.id),
            'model_id': str(self.model_id),
            'name': self.name,
            'description': self.description,
            'notation': self.notation,
            'notation_config': self.notation_config,
            'visible_concepts': [str(c) for c in self.visible_concepts] if self.visible_concepts else [],
            'settings': self.settings,
            'is_default': self.is_default,
            'is_valid': self.is_valid,
            'validation_errors': self.validation_errors,
            'last_validated_at': self.last_validated_at.isoformat() if self.last_validated_at else None,
            'created_by': str(self.created_by),
            'updated_by': str(self.updated_by) if self.updated_by else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_deleted': self.is_deleted,
        }