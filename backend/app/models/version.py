# backend/app/models/version.py
"""
Version Database Model - Complete and Fixed
Path: backend/app/models/version.py
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, JSON, Integer, UniqueConstraint
from sqlalchemy.orm import relationship
import uuid

from app.db.base import Base


class Version(Base):
    """Version model for tracking model/diagram versions"""
    
    __tablename__ = "versions"
    
    # Add unique constraint for entity + version number
    __table_args__ = (
        UniqueConstraint('entity_type', 'entity_id', 'version_number', name='uq_entity_version'),
    )
    
    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    
    # Versioned entity
    entity_type = Column(String(50), nullable=False, index=True)
    # Supported types: model, diagram
    entity_id = Column(String(36), nullable=False, index=True)
    
    # Version info
    version_number = Column(Integer, nullable=False, index=True)
    name = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    
    # Tags for semantic versioning or custom tags
    tags = Column(JSON, nullable=True, default=lambda: [])
    # Example: ["v1.0.0", "stable", "production"]
    
    # Snapshot data - complete state at this version
    snapshot_data = Column(JSON, nullable=False, default=lambda: {})
    
    # Change summary
    changes = Column(JSON, nullable=True, default=lambda: {})
    # Example: {"added": [], "modified": [], "removed": []}
    
    # Version metadata
    meta_data = Column('metadata', JSON, nullable=False, default=lambda: {})
    
    # Audit - FIXED: now String(36) to match User model
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by], backref="versions_created")
    
    def __repr__(self):
        return f"<Version(id={self.id}, entity={self.entity_type}:{self.entity_id}, version={self.version_number})>"
    
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