# backend/app/models/version.py
"""
Version Database Model - COMPLETE Implementation
Path: backend/app/models/version.py
"""
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

from app.db.base import Base


class Version(Base):
    """
    Version model for tracking model history and changes
    
    Versions are immutable snapshots of models at specific points in time.
    """
    
    __tablename__ = "versions"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Foreign key
    model_id = Column(UUID(as_uuid=True), ForeignKey("models.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Version information
    version_number = Column(String(20), nullable=False, index=True)  # e.g., "1.0.0", "2.1.3"
    version_tag = Column(String(100), nullable=True)  # e.g., "v1.0-beta"
    
    # Snapshot data
    snapshot_data = Column(JSONB, nullable=False)  # Complete model snapshot
    diagram_snapshots = Column(JSONB, default=list, server_default='[]')  # All diagram snapshots
    
    # Change information
    change_summary = Column(Text, nullable=True)
    change_log = Column(JSONB, default=list, server_default='[]')  # Detailed changes
    
    # Statistics at this version
    statistics_snapshot = Column(JSONB, default=dict, server_default='{}')
    
    # Parent version (for tracking lineage)
    parent_version_id = Column(UUID(as_uuid=True), ForeignKey("versions.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Commit information
    commit_message = Column(Text, nullable=True)
    commit_hash = Column(String(64), nullable=True, unique=True, index=True)  # SHA256 hash
    
    # Publishing information
    is_published = Column(Boolean, default=False, nullable=False)
    published_to_workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="SET NULL"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    
    # Relationships
    model = relationship("Model", back_populates="versions")
    parent_version = relationship("Version", remote_side=[id], backref="child_versions")
    creator = relationship("User")
    published_to_workspace = relationship("Workspace")
    
    def __repr__(self):
        return f"<Version(id={self.id}, model_id={self.model_id}, version='{self.version_number}')>"
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': str(self.id),
            'model_id': str(self.model_id),
            'version_number': self.version_number,
            'version_tag': self.version_tag,
            'snapshot_data': self.snapshot_data,
            'diagram_snapshots': self.diagram_snapshots,
            'change_summary': self.change_summary,
            'change_log': self.change_log,
            'statistics_snapshot': self.statistics_snapshot,
            'parent_version_id': str(self.parent_version_id) if self.parent_version_id else None,
            'commit_message': self.commit_message,
            'commit_hash': self.commit_hash,
            'is_published': self.is_published,
            'published_to_workspace_id': str(self.published_to_workspace_id) if self.published_to_workspace_id else None,
            'created_by': str(self.created_by),
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }