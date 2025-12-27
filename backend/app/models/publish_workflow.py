"""
Publish Workflow Database Model
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Boolean
import uuid

from app.db.base import Base


class PublishWorkflow(Base):
    """Publish workflow model for model publication approval"""
    
    __tablename__ = "publish_workflows"
    
    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    
    # Model being published
    model_id = Column(String(36), ForeignKey("models.id"), nullable=False, index=True)
    
    # Status: pending, approved, rejected
    status = Column(String(50), nullable=False, default="pending", index=True)
    
    # Request details
    request_message = Column(Text, nullable=True)
    review_message = Column(Text, nullable=True)
    
    # Approval
    is_approved = Column(Boolean, default=False, nullable=False)
    
    # Audit
    requested_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    requested_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    reviewed_at = Column(DateTime, nullable=True)
    reviewed_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    
    def __repr__(self):
        return f"<PublishWorkflow(id={self.id}, status={self.status})>"
