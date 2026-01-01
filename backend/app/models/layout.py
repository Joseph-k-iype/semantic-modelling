# backend/app/models/layout.py
"""
Layout Database Models - COMPLETE Implementation
Path: backend/app/models/layout.py
"""
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text, Enum as SQLEnum, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
import enum

from app.db.base import Base


class LayoutType(str, enum.Enum):
    """Layout type enumeration"""
    MANUAL = "MANUAL"
    LAYERED = "LAYERED"
    FORCE_DIRECTED = "FORCE_DIRECTED"
    BPMN_SWIMLANE = "BPMN_SWIMLANE"
    UML_SEQUENCE = "UML_SEQUENCE"
    STATE_MACHINE = "STATE_MACHINE"


class Layout(Base):
    """
    Layout model - user-controlled diagram layouts
    
    Layouts are independent of diagrams and can be switched/saved/restored.
    Multiple layouts can exist for the same diagram.
    """
    
    __tablename__ = "layouts"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Foreign key
    diagram_id = Column(UUID(as_uuid=True), ForeignKey("diagrams.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Basic information
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Layout type and algorithm
    layout_type = Column(
        SQLEnum(LayoutType, name="layout_type", create_type=False, native_enum=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False, index=True
    )
    
    # Layout data (node positions, edge routing)
    layout_data = Column(JSONB, default=dict, server_default='{}')
    
    # Layout constraints and settings
    constraints = Column(JSONB, default=dict, server_default='{}')
    settings = Column(JSONB, default=dict, server_default='{}')
    
    # Status
    is_active = Column(Boolean, default=False, nullable=False, index=True)  # Currently active layout
    is_auto_apply = Column(Boolean, default=False, nullable=False)  # Auto-apply on diagram load
    
    # Timestamps
    deleted_at = Column(DateTime, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Audit trail
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Constraints
    __table_args__ = (
        CheckConstraint("LENGTH(TRIM(name)) >= 1 AND LENGTH(name) <= 255", name="layouts_name_check"),
        UniqueConstraint('diagram_id', 'name', 'deleted_at', name='layouts_unique_name'),
    )
    
    # Relationships
    diagram = relationship("Diagram", back_populates="layouts")
    snapshots = relationship("LayoutSnapshot", back_populates="layout", cascade="all, delete-orphan")
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    
    def __repr__(self):
        return f"<Layout(id={self.id}, name='{self.name}', type='{self.layout_type.value}')>"
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': str(self.id),
            'diagram_id': str(self.diagram_id),
            'name': self.name,
            'description': self.description,
            'layout_type': self.layout_type.value,
            'layout_data': self.layout_data,
            'constraints': self.constraints,
            'settings': self.settings,
            'is_active': self.is_active,
            'is_auto_apply': self.is_auto_apply,
            'created_by': str(self.created_by),
            'updated_by': str(self.updated_by) if self.updated_by else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class LayoutSnapshot(Base):
    """Layout snapshot for history and rollback"""
    
    __tablename__ = "layout_snapshots"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign key
    layout_id = Column(UUID(as_uuid=True), ForeignKey("layouts.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Snapshot information
    snapshot_name = Column(String(255), nullable=True)
    layout_data = Column(JSONB, nullable=False)
    meta_data = Column(JSONB, default=dict, server_default='{}')
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    
    # Constraints
    __table_args__ = (
        CheckConstraint("snapshot_name IS NULL OR LENGTH(TRIM(snapshot_name)) >= 1", name="layout_snapshots_snapshot_name_check"),
    )
    
    # Relationships
    layout = relationship("Layout", back_populates="snapshots")
    creator = relationship("User")
    
    def __repr__(self):
        return f"<LayoutSnapshot(id={self.id}, layout_id={self.layout_id})>"
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': str(self.id),
            'layout_id': str(self.layout_id),
            'snapshot_name': self.snapshot_name,
            'layout_data': self.layout_data,
            'meta_data': self.meta_data,
            'created_by': str(self.created_by),
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }