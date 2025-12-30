# backend/app/models/comment.py
"""
Comment Database Model - COMPLETE AND FIXED
Path: backend/app/models/comment.py
"""
from datetime import datetime
from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

from app.db.base import Base


class Comment(Base):
    """Comment model for collaboration on models and diagrams"""
    
    __tablename__ = "comments"
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    
    # Comment content
    content = Column(Text, nullable=False)
    
    # Target entity (what is being commented on)
    entity_type = Column(String(50), nullable=False, index=True)
    # Supported types: model, diagram, node, edge, concept, relationship
    entity_id = Column(String(255), nullable=False, index=True)
    
    # Optional: specific location/element within entity
    element_id = Column(String(100), nullable=True)  # e.g., node ID within diagram
    
    # Threading support for nested comments
    parent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("comments.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    thread_id = Column(String(255), nullable=True, index=True)  # Top-level comment ID for grouping
    
    # Status and resolution
    is_resolved = Column(Boolean, default=False, nullable=False)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Reactions/likes count
    reaction_count = Column(Integer, default=0, nullable=False)
    
    # Ownership
    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    updated_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
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
        nullable=True,
        onupdate=datetime.utcnow
    )
    deleted_at = Column(DateTime, nullable=True)  # Soft delete
    
    # Relationships
    parent = relationship(
        "Comment",
        remote_side=[id],
        backref="replies",
        foreign_keys=[parent_id]
    )
    creator = relationship(
        "User",
        foreign_keys=[created_by],
        backref="created_comments"
    )
    updater = relationship(
        "User",
        foreign_keys=[updated_by]
    )
    resolver = relationship(
        "User",
        foreign_keys=[resolved_by]
    )
    
    def __repr__(self):
        return f"<Comment(id={self.id}, entity_type='{self.entity_type}', resolved={self.is_resolved})>"
    
    @property
    def is_deleted(self):
        """Check if comment has been soft-deleted"""
        return self.deleted_at is not None
    
    @property
    def has_replies(self):
        """Check if comment has replies"""
        return len(self.replies) > 0 if hasattr(self, 'replies') else False