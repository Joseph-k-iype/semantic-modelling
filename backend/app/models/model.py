# backend/app/models/model.py
"""
Model Database Models - COMPLETE Implementation
Path: backend/app/models/model.py

Models:
- Model: Semantic model metadata (actual model stored in FalkorDB)
- ModelStatistics: Denormalized statistics for performance
- ModelTag: Tags for model categorization
"""
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
import uuid
import enum

from app.db.base import Base


class ModelType(str, enum.Enum):
    """Model type enumeration"""
    ER = "ER"
    UML_CLASS = "UML_CLASS"
    UML_SEQUENCE = "UML_SEQUENCE"
    UML_ACTIVITY = "UML_ACTIVITY"
    UML_STATE = "UML_STATE"
    UML_COMPONENT = "UML_COMPONENT"
    UML_DEPLOYMENT = "UML_DEPLOYMENT"
    UML_PACKAGE = "UML_PACKAGE"
    BPMN = "BPMN"
    MIXED = "MIXED"


class ModelStatus(str, enum.Enum):
    """Model status enumeration"""
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"
    PUBLISHED = "PUBLISHED"


class Model(Base):
    """
    Model metadata - actual semantic model stored in FalkorDB graph database
    
    This table stores metadata and pointers to the graph database.
    The actual semantic model (concepts, relationships, etc.) is in FalkorDB.
    
    Model Types:
    - ER: Entity-Relationship diagram
    - UML_CLASS: UML Class diagram
    - UML_SEQUENCE: UML Sequence diagram
    - UML_ACTIVITY: UML Activity diagram
    - UML_STATE: UML State Machine diagram
    - UML_COMPONENT: UML Component diagram
    - UML_DEPLOYMENT: UML Deployment diagram
    - UML_PACKAGE: UML Package diagram
    - BPMN: Business Process Model and Notation
    - MIXED: Multiple notation types
    """
    
    __tablename__ = "models"
    
    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    
    # Foreign keys
    workspace_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    folder_id = Column(
        UUID(as_uuid=True),
        ForeignKey("folders.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # Basic information
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Model type - must match one of the allowed types
    model_type = Column(String(50), nullable=False, index=True)
    
    # Graph database identifier - unique reference to FalkorDB graph
    graph_id = Column(String(255), unique=True, nullable=False, index=True)
    
    # Settings and additional data
    meta_data = Column(JSONB, nullable=False, default=dict, server_default='{}')
    settings = Column(JSONB, nullable=False, default=dict, server_default='{}')
    validation_rules = Column(JSONB, nullable=False, default=list, server_default='[]')
    
    # Publishing information
    is_published = Column(Boolean, default=False, nullable=False, index=True)
    published_at = Column(DateTime, nullable=True)
    published_version = Column(String(20), nullable=True)
    
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
            name="models_name_check"
        ),
        CheckConstraint(
            "model_type IN ('ER', 'UML_CLASS', 'UML_SEQUENCE', 'UML_ACTIVITY', 'UML_STATE', 'UML_COMPONENT', 'UML_DEPLOYMENT', 'UML_PACKAGE', 'BPMN', 'MIXED')",
            name="models_model_type_check"
        ),
        CheckConstraint(
            "LENGTH(graph_id) >= 1",
            name="models_graph_id_check"
        ),
        UniqueConstraint('workspace_id', 'folder_id', 'name', 'deleted_at', name='models_unique_name'),
    )
    
    # Relationships
    workspace = relationship("Workspace", back_populates="models")
    folder = relationship("Folder")
    diagrams = relationship("Diagram", back_populates="model", cascade="all, delete-orphan")
    versions = relationship("Version", back_populates="model", cascade="all, delete-orphan")
    statistics = relationship("ModelStatistics", back_populates="model", uselist=False, cascade="all, delete-orphan")
    tags = relationship("ModelTag", back_populates="model", cascade="all, delete-orphan")
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    
    def __repr__(self):
        return f"<Model(id={self.id}, name='{self.name}', type='{self.model_type}')>"
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': str(self.id),
            'workspace_id': str(self.workspace_id),
            'folder_id': str(self.folder_id) if self.folder_id else None,
            'name': self.name,
            'description': self.description,
            'model_type': self.model_type,
            'graph_id': self.graph_id,
            'meta_data': self.meta_data,
            'settings': self.settings,
            'is_published': self.is_published,
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'published_version': self.published_version,
            'created_by': str(self.created_by),
            'updated_by': str(self.updated_by) if self.updated_by else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class ModelStatistics(Base):
    """
    Model statistics - denormalized for performance
    
    This table caches statistics about models to avoid expensive
    graph queries for common operations.
    """
    
    __tablename__ = "model_statistics"
    
    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    
    # Foreign key to model (one-to-one relationship)
    model_id = Column(
        UUID(as_uuid=True),
        ForeignKey("models.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )
    
    # Concept counts
    total_concepts = Column(Integer, default=0, nullable=False)
    entity_count = Column(Integer, default=0, nullable=False)
    class_count = Column(Integer, default=0, nullable=False)
    interface_count = Column(Integer, default=0, nullable=False)
    component_count = Column(Integer, default=0, nullable=False)
    
    # Relationship counts
    total_relationships = Column(Integer, default=0, nullable=False)
    association_count = Column(Integer, default=0, nullable=False)
    inheritance_count = Column(Integer, default=0, nullable=False)
    dependency_count = Column(Integer, default=0, nullable=False)
    
    # Attribute counts
    total_attributes = Column(Integer, default=0, nullable=False)
    
    # Diagram counts
    diagram_count = Column(Integer, default=0, nullable=False)
    
    # Complexity metrics
    max_depth = Column(Integer, default=0, nullable=False)
    avg_relationships_per_concept = Column(Integer, default=0, nullable=False)
    
    # Timestamps
    last_calculated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    model = relationship("Model", back_populates="statistics")
    
    def __repr__(self):
        return f"<ModelStatistics(model_id={self.model_id}, concepts={self.total_concepts}, relationships={self.total_relationships})>"
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': str(self.id),
            'model_id': str(self.model_id),
            'total_concepts': self.total_concepts,
            'entity_count': self.entity_count,
            'class_count': self.class_count,
            'interface_count': self.interface_count,
            'component_count': self.component_count,
            'total_relationships': self.total_relationships,
            'association_count': self.association_count,
            'inheritance_count': self.inheritance_count,
            'dependency_count': self.dependency_count,
            'total_attributes': self.total_attributes,
            'diagram_count': self.diagram_count,
            'max_depth': self.max_depth,
            'avg_relationships_per_concept': self.avg_relationships_per_concept,
            'last_calculated_at': self.last_calculated_at.isoformat() if self.last_calculated_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class ModelTag(Base):
    """
    Model tags for categorization and organization
    """
    
    __tablename__ = "model_tags"
    
    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    
    # Foreign key
    model_id = Column(
        UUID(as_uuid=True),
        ForeignKey("models.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Tag information
    tag = Column(String(50), nullable=False, index=True)
    color = Column(String(7), nullable=True)  # Hex color code
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            "LENGTH(TRIM(tag)) >= 1 AND LENGTH(tag) <= 50",
            name="model_tags_tag_check"
        ),
        UniqueConstraint('model_id', 'tag', name='model_tags_unique'),
    )
    
    # Relationship
    model = relationship("Model", back_populates="tags")
    
    def __repr__(self):
        return f"<ModelTag(model_id={self.model_id}, tag='{self.tag}')>"
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': str(self.id),
            'model_id': str(self.model_id),
            'tag': self.tag,
            'color': self.color,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }