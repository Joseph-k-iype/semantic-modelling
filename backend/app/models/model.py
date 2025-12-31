# backend/app/models/model.py
"""
Model Database Model - COMPLETE matching actual database schema
Path: backend/app/models/model.py
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Integer, ARRAY
from sqlalchemy.orm import relationship, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

from app.db.base import Base


class Model(Base):
    """
    Model represents a semantic business model
    
    CRITICAL: Columns must match database/postgres/schema/04-models.sql
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
    type = Column(String(50), nullable=False, default='ER', index=True)
    # type options: ER, UML, BPMN, CUSTOM
    
    # Status and versioning
    status = Column(String(50), default='draft', nullable=False, index=True)
    # status options: draft, in_review, published, archived
    version = Column(Integer, default=1, nullable=False)
    
    # Tags for categorization (PostgreSQL TEXT array in database)
    tags = Column(ARRAY(Text), default=list)
    
    # Metadata (JSONB for flexible storage)
    metadata_col = mapped_column("metadata", JSONB, default=dict)
    
    # Ownership and audit - All UUID foreign keys
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
    
    last_edited_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, index=True)
    last_edited_at = Column(DateTime, nullable=True)
    
    # Publishing info (from database schema)
    published_at = Column(DateTime, nullable=True)
    published_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # ❌ REMOVED: deleted_at does NOT exist in database schema
    # The database schema does not have soft delete for models
    
    # Relationships - Using backref to avoid circular dependency
    diagrams = relationship(
        "Diagram",
        backref="model",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    
    workspace = relationship("Workspace", foreign_keys=[workspace_id], backref="models")
    folder = relationship("Folder", foreign_keys=[folder_id], backref="models")
    creator = relationship("User", foreign_keys=[created_by], backref="created_models")
    updater = relationship("User", foreign_keys=[updated_by])
    last_editor = relationship("User", foreign_keys=[last_edited_by])
    publisher = relationship("User", foreign_keys=[published_by])
    
    def __repr__(self):
        return f"<Model(id={self.id}, name='{self.name}', type='{self.type}')>"
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': str(self.id),
            'name': self.name,
            'description': self.description,
            'type': self.type,
            'status': self.status,
            'version': self.version,
            'workspace_id': str(self.workspace_id),
            'folder_id': str(self.folder_id) if self.folder_id else None,
            'tags': self.tags or [],
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
        return self.diagrams.count() if hasattr(self, 'diagrams') else 0