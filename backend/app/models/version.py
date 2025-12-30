# backend/app/models/version.py
"""
Version Database Model - FIXED with UUID types
Path: backend/app/models/version.py
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Integer, UniqueConstraint
from sqlalchemy.orm import relationship, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

from app.db.base import Base


class Version(Base):
    """Version model for tracking model/diagram versions"""
    
    __tablename__ = "versions"
    
    # Add unique constraint for entity + version number
    __table_args__ = (
        UniqueConstraint('entity_type', 'entity_id', 'version_number', name='uq_entity_version'),
    )
    
    # Primary key - FIXED: UUID type
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    
    # Versioned entity
    entity_type = Column(String(50), nullable=False, index=True)
    # Supported types: model, diagram
    
    # FIXED: UUID for entity_id to match models/diagrams
    entity_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Version info
    version_number = Column(Integer, nullable=False, index=True)
    name = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    
    # Tags for semantic versioning or custom tags (JSONB for better performance)
    tags = Column(JSONB, nullable=True, default=list)
    # Example: ["v1.0.0", "stable", "production"]
    
    # Snapshot data - complete state at this version (JSONB)
    snapshot_data = Column(JSONB, nullable=False, default=dict)
    
    # Change summary (JSONB)
    changes = Column(JSONB, nullable=True, default=dict)
    # Example: {"added": [], "modified": [], "removed": []}
    
    # Version metadata (JSONB, using mapped_column to avoid conflict with 'metadata')
    meta_data = mapped_column("metadata", JSONB, nullable=False, default=dict)
    
    # Audit - FIXED: UUID type to match User model
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=False,
        index=True
    )
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by], backref="versions_created")
    
    def __repr__(self):
        return f"<Version(id={self.id}, entity={self.entity_type}:{self.entity_id}, version={self.version_number})>"
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': str(self.id),
            'entity_type': self.entity_type,
            'entity_id': str(self.entity_id),
            'version_number': self.version_number,
            'name': self.name,
            'description': self.description,
            'tags': self.tags,
            'created_by': str(self.created_by),
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
    
    @property
    def version_tag(self):
        """Get the first tag as version identifier"""
        return self.tags[0] if self.tags else f"v{self.version_number}"
    
    @property
    def is_tagged(self):
        """Check if this version has any tags"""
        return bool(self.tags)
    
    @property
    def change_count(self):
        """Get total number of changes in this version"""
        if not self.changes:
            return 0
        return (
            len(self.changes.get("added", [])) +
            len(self.changes.get("modified", [])) +
            len(self.changes.get("removed", []))
        )