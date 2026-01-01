# backend/app/models/comment.py
"""
Comment Database Models - COMPLETE Implementation
Path: backend/app/models/comment.py
"""
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text, Enum as SQLEnum, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
import enum

from app.db.base import Base


class EntityType(str, enum.Enum):
    """Entity type for comments"""
    MODEL = "MODEL"
    DIAGRAM = "DIAGRAM"
    CONCEPT = "CONCEPT"
    RELATIONSHIP = "RELATIONSHIP"


class Comment(Base):
    """
    Comment model for collaboration and discussion
    
    Comments can be attached to any entity (model, diagram, concept, relationship).
    Supports threaded comments (parent-child relationships).
    """
    
    __tablename__ = "comments"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Entity reference (polymorphic)
    entity_type = Column(
        SQLEnum(EntityType, name="entity_type", create_type=False, native_enum=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False, index=True
    )
    entity_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Threading
    parent_id = Column(UUID(as_uuid=True), ForeignKey("comments.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # Content
    content = Column(Text, nullable=False)
    
    # Resolution status (for review/approval workflows)
    is_resolved = Column(Boolean, default=False, nullable=False, index=True)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Position (for diagram annotations)
    position = Column(JSONB, nullable=True)  # {x, y} coordinates on diagram
    
    # Attachments and additional data
    attachments = Column(JSONB, default=list, server_default='[]')
    meta_data = Column(JSONB, default=dict, server_default='{}')
    
    # Edit tracking
    edited = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    deleted_at = Column(DateTime, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Audit trail
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Constraints
    __table_args__ = (
        CheckConstraint("LENGTH(TRIM(content)) >= 1", name="comments_content_check"),
        CheckConstraint(
            "(is_resolved = FALSE AND resolved_at IS NULL AND resolved_by IS NULL) OR (is_resolved = TRUE AND resolved_at IS NOT NULL)",
            name="comments_resolved_check"
        ),
    )
    
    # Relationships
    parent = relationship("Comment", remote_side=[id], backref="replies")
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    resolver = relationship("User", foreign_keys=[resolved_by])
    mentions = relationship("CommentMention", back_populates="comment", cascade="all, delete-orphan")
    reactions = relationship("CommentReaction", back_populates="comment", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Comment(id={self.id}, entity_type='{self.entity_type.value}', entity_id={self.entity_id})>"
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': str(self.id),
            'entity_type': self.entity_type.value,
            'entity_id': str(self.entity_id),
            'parent_id': str(self.parent_id) if self.parent_id else None,
            'content': self.content,
            'is_resolved': self.is_resolved,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'resolved_by': str(self.resolved_by) if self.resolved_by else None,
            'position': self.position,
            'attachments': self.attachments,
            'meta_data': self.meta_data,
            'edited': self.edited,
            'created_by': str(self.created_by),
            'updated_by': str(self.updated_by) if self.updated_by else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class CommentMention(Base):
    """Comment mentions for @username notifications"""
    
    __tablename__ = "comment_mentions"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    comment_id = Column(UUID(as_uuid=True), ForeignKey("comments.id", ondelete="CASCADE"), nullable=False, index=True)
    mentioned_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Read status
    is_read = Column(Boolean, default=False, nullable=False)
    read_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('comment_id', 'mentioned_user_id', name='comment_mentions_unique'),
    )
    
    # Relationships
    comment = relationship("Comment", back_populates="mentions")
    mentioned_user = relationship("User")
    
    def __repr__(self):
        return f"<CommentMention(comment_id={self.comment_id}, user_id={self.mentioned_user_id})>"
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': str(self.id),
            'comment_id': str(self.comment_id),
            'mentioned_user_id': str(self.mentioned_user_id),
            'is_read': self.is_read,
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class CommentReaction(Base):
    """Comment reactions (emoji reactions)"""
    
    __tablename__ = "comment_reactions"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    comment_id = Column(UUID(as_uuid=True), ForeignKey("comments.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Reaction
    emoji = Column(String(20), nullable=False)  # Unicode emoji
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('comment_id', 'user_id', 'emoji', name='comment_reactions_unique'),
    )
    
    # Relationships
    comment = relationship("Comment", back_populates="reactions")
    user = relationship("User")
    
    def __repr__(self):
        return f"<CommentReaction(comment_id={self.comment_id}, emoji='{self.emoji}')>"
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': str(self.id),
            'comment_id': str(self.comment_id),
            'user_id': str(self.user_id),
            'emoji': self.emoji,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }