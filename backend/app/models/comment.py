# backend/app/models/comment.py
"""
Comment Database Model - Complete and Fixed
Path: backend/app/models/comment.py
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Boolean, Integer
from sqlalchemy.orm import relationship
import uuid

from app.db.base import Base


class Comment(Base):
    """Comment model for collaboration on models and diagrams"""
    
    __tablename__ = "comments"
    
    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    
    # Comment content
    content = Column(Text, nullable=False)
    
    # Target entity (what is being commented on)
    entity_type = Column(String(50), nullable=False, index=True)
    # Supported types: model, diagram, node, edge, concept, relationship
    entity_id = Column(String(36), nullable=False, index=True)
    
    # Optional: specific location/element within entity
    element_id = Column(String(100), nullable=True)  # e.g., node ID within diagram
    
    # Threading support for nested comments
    parent_id = Column(String(36), ForeignKey("comments.id"), nullable=True, index=True)
    thread_id = Column(String(36), nullable=True, index=True)  # Top-level comment ID for grouping
    
    # Status and resolution
    is_resolved = Column(Boolean, default=False, nullable=False)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    
    # Reactions/likes count
    reaction_count = Column(Integer, default=0, nullable=False)
    
    # Ownership - FIXED: now String(36) to match User model
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    updated_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=True, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)  # Soft delete
    
    # Relationships
    parent = relationship(
        "Comment",
        remote_side=[id],
        backref="replies",
        foreign_keys=[parent_id]
    )
    user = relationship(
        "User",
        foreign_keys=[created_by],
        backref="comments"
    )
    resolver = relationship(
        "User",
        foreign_keys=[resolved_by]
    )
    updater = relationship(
        "User",
        foreign_keys=[updated_by]
    )
    
    def __repr__(self):
        return f"<Comment(id={self.id}, entity={self.entity_type}:{self.entity_id}, resolved={self.is_resolved})>"
    
    @property
    def is_top_level(self):
        """Check if this is a top-level comment (not a reply)"""
        return self.parent_id is None
    
    @property
    def is_deleted(self):
        """Check if this comment has been soft-deleted"""
        return self.deleted_at is not None
    
    @property
    def reply_count(self):
        """Get the number of direct replies to this comment"""
        return len(self.replies) if hasattr(self, 'replies') else 0