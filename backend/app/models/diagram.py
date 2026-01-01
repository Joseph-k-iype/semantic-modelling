# backend/app/models/diagram.py
"""
Diagram Database Model - COMPLETE Implementation
Path: backend/app/models/diagram.py

Diagrams are visual projections of semantic models.
Multiple diagrams can represent the same model in different notations.
"""
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
import enum

from app.db.base import Base


class NotationType(str, enum.Enum):
    """Notation type enumeration"""
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
    
    # Notation type - determines how the model is visualized
    notation_type = Column(String(50), nullable=False, index=True)
    
    # Diagram data (nodes, edges, positions in React Flow format)
    diagram_data = Column(JSONB, nullable=False, default=dict, server_default='{}')
    
    # Settings and additional data
    settings = Column(JSONB, nullable=False, default=dict, server_default='{}')
    meta_data = Column(JSONB, nullable=False, default=dict, server_default='{}')
    
    # Validation state
    validation_errors = Column(JSONB, nullable=False, default=list, server_default='[]')
    is_valid = Column(Boolean, default=True, nullable=False)
    last_validated_at = Column(DateTime, nullable=True)
    
    # Viewport state (for preserving zoom and pan)
    viewport = Column(JSONB, nullable=False, default=dict, server_default='{"x": 0, "y": 0, "zoom": 1}')
    
    # Thumbnail for quick preview
    thumbnail_url = Column(Text, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    
    # Timestamps
    deleted_at = Column(DateTime, nullable=True, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Audit trail
    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    
    updated_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            "LENGTH(TRIM(name)) >= 1 AND LENGTH(name) <= 255",
            name="diagrams_name_check"
        ),
        CheckConstraint(
            "notation_type IN ('ER', 'UML_CLASS', 'UML_SEQUENCE', 'UML_ACTIVITY', 'UML_STATE', 'UML_COMPONENT', 'UML_DEPLOYMENT', 'UML_PACKAGE', 'BPMN')",
            name="diagrams_notation_type_check"
        ),
        UniqueConstraint('model_id', 'name', 'deleted_at', name='diagrams_unique_name'),
    )
    
    # Relationships
    model = relationship("Model", back_populates="diagrams")
    layouts = relationship("Layout", back_populates="diagram", cascade="all, delete-orphan")
    comments = relationship("Comment", cascade="all, delete-orphan", 
                          primaryjoin="and_(Diagram.id==Comment.entity_id, Comment.entity_type=='DIAGRAM')",
                          foreign_keys="Comment.entity_id")
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    
    def __repr__(self):
        return f"<Diagram(id={self.id}, name='{self.name}', notation='{self.notation_type}')>"
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': str(self.id),
            'model_id': str(self.model_id),
            'name': self.name,
            'description': self.description,
            'notation_type': self.notation_type,
            'diagram_data': self.diagram_data,
            'settings': self.settings,
            'meta_data': self.meta_data,
            'validation_errors': self.validation_errors,
            'is_valid': self.is_valid,
            'last_validated_at': self.last_validated_at.isoformat() if self.last_validated_at else None,
            'viewport': self.viewport,
            'thumbnail_url': self.thumbnail_url,
            'is_active': self.is_active,
            'created_by': str(self.created_by),
            'updated_by': str(self.updated_by) if self.updated_by else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }