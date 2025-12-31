# backend/app/models/model.py
"""
Model Database Model - COMPLETE matching actual database schema
Path: backend/app/models/model.py
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Integer, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
import uuid
import enum

from app.db.base import Base


class ModelType(str, enum.Enum):
    """Model type enumeration"""
    ER = "ER"
    UML = "UML"
    BPMN = "BPMN"
    CUSTOM = "CUSTOM"


class ModelStatus(str, enum.Enum):
    """Model status enumeration"""
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class Model(Base):
    """
    Model represents a semantic business model
    
    CRITICAL: Columns must match database/postgres/schema/04-models.sql
    NOTE: Use meta_data attribute in Python code (maps to 'metadata' column in DB)
    """
    
    __tablename__ = "models"
    
    # Primary key - UUID
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    
    # Relationships - All foreign keys use UUID
    workspace_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,  # NOT NULL in database
        index=True
    )
    
    folder_id = Column(
        UUID(as_uuid=True),
        ForeignKey("folders.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # Model details
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Model type - Using SQLEnum for PostgreSQL ENUM with proper value handling
    type = Column(
        SQLEnum(
            ModelType,
            name="model_type",
            create_type=False,
            native_enum=False,  # ✅ Use enum values, not names
            values_callable=lambda x: [e.value for e in x]
        ),
        nullable=False,
        default=ModelType.ER,
        index=True
    )
    
    # Status and versioning
    status = Column(
        SQLEnum(
            ModelStatus,
            name="model_status",
            create_type=False,
            native_enum=False,  # ✅ Use enum values, not names
            values_callable=lambda x: [e.value for e in x]
        ),
        nullable=False,
        default=ModelStatus.DRAFT,
        index=True
    )
    
    version = Column(Integer, default=1, nullable=False)
    
    # Tags for categorization
    tags = Column(ARRAY(String), nullable=False, default=list)
    
    # CRITICAL FIX: 'metadata' is reserved by SQLAlchemy
    # Use 'meta_data' in Python but map to 'metadata' column in database
    # DO NOT add @property for metadata - it will shadow SQLAlchemy's class attribute
    meta_data = Column('metadata', JSONB, nullable=False, default=dict)
    
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
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    last_edited_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    
    last_edited_at = Column(DateTime, nullable=True)
    
    # Publishing info
    published_at = Column(DateTime, nullable=True)
    published_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Relationships
    workspace = relationship("Workspace", foreign_keys=[workspace_id], backref="models")
    folder = relationship("Folder", foreign_keys=[folder_id], backref="models")
    creator = relationship("User", foreign_keys=[created_by], backref="created_models")
    updater = relationship("User", foreign_keys=[updated_by])
    last_editor = relationship("User", foreign_keys=[last_edited_by])  # ✅ FIXED: Use column name
    publisher = relationship("User", foreign_keys=[published_by])
    
    def __repr__(self):
        return f"<Model(id={self.id}, name='{self.name}', type='{self.type.value if isinstance(self.type, ModelType) else self.type}')>"
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': str(self.id),
            'name': self.name,
            'description': self.description,
            'type': self.type.value if isinstance(self.type, ModelType) else self.type,
            'status': self.status.value if isinstance(self.status, ModelStatus) else self.status,
            'version': self.version,
            'workspace_id': str(self.workspace_id),
            'folder_id': str(self.folder_id) if self.folder_id else None,
            'tags': self.tags or [],
            'metadata': self.meta_data,  # Return as 'metadata' in API responses
            'created_by': str(self.created_by),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'published_at': self.published_at.isoformat() if self.published_at else None,
        }
    
    @property
    def is_published(self):
        """Check if model has been published"""
        return self.published_at is not None
    
    @property
    def diagram_count(self):
        """Get the number of diagrams for this model"""
        return len(self.diagrams) if hasattr(self, 'diagrams') else 0