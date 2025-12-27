"""
Comment Database Model
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Boolean
import uuid

from app.db.base import Base


class Comment(Base):
    """Comment model for diagram annotations"""
    
    __tablename__ = "comments"
    
    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    
    # Comment target
    entity_type = Column(String(50), nullable=False, index=True)  # diagram, node, edge
    entity_id = Column(String(36), nullable=False, index=True)
    
    # Comment content
    content = Column(Text, nullable=False)
    is_resolved = Column(Boolean, default=False, nullable=False)
    
    # Parent comment for threads
    parent_comment_id = Column(String(36), ForeignKey("comments.id"), nullable=True, index=True)
    
    # Audit
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    
    def __repr__(self):
        return f"<Comment(id={self.id}, entity={self.entity_type})>"