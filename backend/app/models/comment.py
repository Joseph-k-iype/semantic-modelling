# backend/app/models/comment.py
"""
Comment Database Model - FIXED
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Boolean, Integer
import uuid

from app.db.base import Base


class Comment(Base):
    """Comment model for inline collaboration on models/diagrams"""
    
    __tablename__ = "comments"
    
    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    
    # Commented entity
    entity_type = Column(String(50), nullable=False, index=True)  # model, diagram, node, edge
    entity_id = Column(String(36), nullable=False, index=True)
    
    # Comment content
    content = Column(Text, nullable=False)
    
    # Thread info
    parent_comment_id = Column(String(36), ForeignKey("comments.id"), nullable=True, index=True)
    is_resolved = Column(Boolean, default=False, nullable=False)
    
    # Position (for node/edge comments) - FIXED: Changed to Integer for coordinates
    position_x = Column(Integer, nullable=True)
    position_y = Column(Integer, nullable=True)
    
    # Audit
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    updated_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    
    # Soft delete
    deleted_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<Comment(id={self.id}, entity={self.entity_type}, resolved={self.is_resolved})>"