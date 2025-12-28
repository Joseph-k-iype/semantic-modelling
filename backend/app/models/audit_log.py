# backend/app/models/audit_log.py
"""
Audit Log Database Model - FIXED
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, JSON
import uuid

from app.db.base import Base


class AuditLog(Base):
    """Audit log model for tracking all system actions"""
    
    __tablename__ = "audit_logs"
    
    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    
    # Action details
    action = Column(String(100), nullable=False, index=True)  # create, update, delete, etc.
    entity_type = Column(String(50), nullable=False, index=True)
    entity_id = Column(String(36), nullable=False, index=True)
    
    # Change details
    changes = Column(JSON, nullable=True, default=lambda: {})
    # FIXED: Use meta_data as Python attribute, 'metadata' as DB column name
    meta_data = Column('metadata', JSON, nullable=True, default=lambda: {})
    
    # Request details
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Audit
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, action={self.action}, entity={self.entity_type})>"