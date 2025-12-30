# backend/app/models/model.py
"""
Model Database Model - FIXED with UUID foreign keys
Path: backend/app/models/model.py
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Integer, ARRAY
from sqlalchemy.orm import relationship, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

from app.db.base import Base


class Model(Base):
    """Model represents a semantic business model"""
    
    __tablename__ = "models"
    
    # Primary key - UUID
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    
    # Relationships - FIXED: All foreign keys now use UUID
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
    
    # Model details
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    type = Column(String(50), nullable=False, default='ER', index=True)
    # type options: ER, UML, BPMN, CUSTOM
    
    # Status and versioning
    status = Column(String(50), default='draft', nullable=False, index=True)
    # status options: draft, in_review, published, archived
    version = Column(Integer, default=1, nullable=False)
    
    # Tags for categorization (PostgreSQL array)
    tags = Column(ARRAY(String), default=list)
    
    # Metadata (JSONB for flexible storage)
    metadata_col = mapped_column("metadata", JSONB, default=dict)
    
    # Ownership and audit - FIXED: All UUID foreign keys
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
    
    # Publishing info
    published_at = Column(DateTime, nullable=True)
    published_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Relationships
    workspace = relationship("Workspace", foreign_keys=[workspace_id])
    folder = relationship("Folder", foreign_keys=[folder_id])
    creator = relationship("User", foreign_keys=[created_by])
    
    def __repr__(self):
        return f"<Model(id={self.id}, name='{self.name}', type='{self.type}')>"
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': str(self.id),
            'workspace_id': str(self.workspace_id),
            'folder_id': str(self.folder_id) if self.folder_id else None,
            'name': self.name,
            'description': self.description,
            'type': self.type,
            'status': self.status,
            'version': self.version,
            'tags': self.tags,
            'created_by': str(self.created_by),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }