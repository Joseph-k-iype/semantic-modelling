# backend/app/models/publish_workflow.py
"""
Publish Workflow Database Model
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, JSON, Boolean
import uuid

from app.db.base import Base


class PublishWorkflow(Base):
    """Publish workflow model for managing model publication approval process"""
    
    __tablename__ = "publish_workflows"
    
    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    
    # Published entity
    entity_type = Column(String(50), nullable=False, index=True)  # model, diagram
    entity_id = Column(String(36), nullable=False, index=True)
    
    # Source and target workspaces
    source_workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False, index=True)
    target_workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False, index=True)
    
    # Workflow status
    status = Column(String(50), nullable=False, default="pending", index=True)  # pending, approved, rejected, cancelled
    
    # Request details
    request_message = Column(Text, nullable=True)
    approval_message = Column(Text, nullable=True)
    
    # Version snapshot
    version_snapshot = Column(JSON, nullable=True, default=lambda: {})
    
    # Audit
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    reviewed_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<PublishWorkflow(id={self.id}, entity={self.entity_type}, status={self.status})>"