# backend/app/models/diagram.py
"""
Diagram Database Model - COMPLETE AND FIXED
Path: backend/app/models/diagram.py

CRITICAL FIX: Includes NotationType enum for imports
STRATEGIC FIX: Added 'graph_name' field for one graph per diagram architecture
"""
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
import uuid
import enum

from app.db.base import Base


# ============================================================================
# NOTATION TYPE ENUM - CRITICAL: Must be defined for imports
# ============================================================================

class NotationType(str, enum.Enum):
    """
    Notation type enumeration
    Matches diagram_notation ENUM in database schema
    """
    ER = "ER"
    UML_CLASS = "UML_CLASS"
    UML_SEQUENCE = "UML_SEQUENCE"
    UML_ACTIVITY = "UML_ACTIVITY"
    UML_STATE = "UML_STATE"
    UML_COMPONENT = "UML_COMPONENT"
    UML_DEPLOYMENT = "UML_DEPLOYMENT"
    UML_PACKAGE = "UML_PACKAGE"
    BPMN = "BPMN"


# ============================================================================
# DIAGRAM MODEL
# ============================================================================

class Diagram(Base):
    """
    Diagram model - visual projection of semantic model
    
    ARCHITECTURE:
    - Each diagram gets its own FalkorDB graph (one-to-one mapping)
    - graph_name stores the reference to the FalkorDB graph
    - Format: user_{username}_workspace_{workspace}_diagram_{diagram_name}
    
    The semantic model itself is stored in FalkorDB (graph database).
    This table stores metadata, notation configuration, visual settings, and graph reference.
    
    Notation Types:
    - ER: Entity-Relationship diagram
    - UML_CLASS: UML Class diagram
    - UML_SEQUENCE: UML Sequence diagram
    - UML_ACTIVITY: UML Activity diagram
    - UML_STATE: UML State Machine diagram
    - UML_COMPONENT: UML Component diagram
    - UML_DEPLOYMENT: UML Deployment diagram
    - UML_PACKAGE: UML Package diagram
    - BPMN: Business Process Model and Notation
    """
    
    __tablename__ = "diagrams"
    
    # ========================================================================
    # PRIMARY KEY
    # ========================================================================
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    
    # ========================================================================
    # FOREIGN KEYS
    # ========================================================================
    
    model_id = Column(
        UUID(as_uuid=True),
        ForeignKey("models.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # ========================================================================
    # BASIC INFORMATION
    # ========================================================================
    
    name = Column(
        String(255),
        nullable=False
    )
    
    description = Column(
        Text,
        nullable=True
    )
    
    # ========================================================================
    # NOTATION (CRITICAL FIX)
    # ========================================================================
    
    # CRITICAL FIX: Column name is 'notation' (NOT 'notation_type')
    # This matches the SQL schema and uses the diagram_notation ENUM type
    notation = Column(
        String(50),
        nullable=False,
        index=True
    )
    
    # ========================================================================
    # FALKORDB GRAPH REFERENCE (STRATEGIC FIX)
    # ========================================================================
    
    # STRATEGIC FIX: FalkorDB graph reference
    # Each diagram gets its own isolated graph in FalkorDB
    # Format: user_{username}_workspace_{workspace}_diagram_{diagram_name}
    # Example: user_john_workspace_engineering_diagram_customer_order_er
    # 
    # This enables:
    # - Complete isolation between diagrams
    # - Easy deletion (delete diagram → delete its graph)
    # - Clear 1:1 mapping (PostgreSQL diagram ↔ FalkorDB graph)
    # - No mixing of entities from different diagrams
    graph_name = Column(
        String(500),
        unique=True,
        nullable=True,  # NULL until first sync to FalkorDB
        index=True
    )
    
    # ========================================================================
    # DIAGRAM CONTENT AND CONFIGURATION
    # ========================================================================
    
    # Notation-specific configuration (swimlanes, lifelines, sequence numbering, etc.)
    notation_config = Column(
        JSONB,
        nullable=False,
        default=dict,
        server_default='{}'
    )
    
    # Array of concept UUIDs visible in this diagram (from FalkorDB)
    # Diagrams can show a subset of the model's concepts
    visible_concepts = Column(
        ARRAY(UUID(as_uuid=True)),
        nullable=False,
        default=list,
        server_default='{}'
    )
    
    # Additional diagram settings (viewport, zoom, grid, style preferences, etc.)
    settings = Column(
        JSONB,
        nullable=False,
        default=dict,
        server_default='{}'
    )
    
    # ========================================================================
    # DIAGRAM FLAGS
    # ========================================================================
    
    # Is this the default diagram for the model?
    is_default = Column(
        Boolean,
        default=False,
        nullable=False,
        index=True
    )
    
    # ========================================================================
    # VALIDATION STATE
    # ========================================================================
    
    # Array of validation error objects from last validation run
    validation_errors = Column(
        JSONB,
        nullable=False,
        default=list,
        server_default='[]'
    )
    
    # Whether the diagram passes all validation rules for its notation type
    is_valid = Column(
        Boolean,
        default=True,
        nullable=False,
        index=True
    )
    
    # Timestamp of last validation run
    last_validated_at = Column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # ========================================================================
    # SOFT DELETE
    # ========================================================================
    
    deleted_at = Column(
        DateTime(timezone=True),
        nullable=True,
        index=True
    )
    
    # ========================================================================
    # AUDIT TRAIL
    # ========================================================================
    
    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    
    updated_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True
    )
    
    created_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        index=True
    )
    
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    # ========================================================================
    # RELATIONSHIPS
    # ========================================================================
    
    # Relationship to parent model
    model = relationship(
        "Model",
        back_populates="diagrams"
    )
    
    # Relationship to layouts (diagram can have multiple layouts)
    layouts = relationship(
        "Layout",
        back_populates="diagram",
        cascade="all, delete-orphan"
    )
    
    # Relationship to creator user
    creator = relationship(
        "User",
        foreign_keys=[created_by],
        backref="created_diagrams"
    )
    
    # Relationship to updater user
    updater = relationship(
        "User",
        foreign_keys=[updated_by],
        backref="updated_diagrams"
    )
    
    # ========================================================================
    # CONSTRAINTS
    # ========================================================================
    
    __table_args__ = (
        CheckConstraint(
            "LENGTH(TRIM(name)) >= 1 AND LENGTH(name) <= 255",
            name="diagrams_name_check"
        ),
    )
    
    # ========================================================================
    # PROPERTIES AND METHODS
    # ========================================================================
    
    def __repr__(self):
        return (
            f"<Diagram(id={self.id}, name='{self.name}', "
            f"notation='{self.notation}', graph_name='{self.graph_name}')>"
        )
    
    @property
    def nodes(self):
        """
        Get nodes from notation_config
        
        Returns list of node dictionaries from the React Flow format
        """
        return self.notation_config.get('nodes', []) if self.notation_config else []
    
    @property
    def edges(self):
        """
        Get edges from notation_config
        
        Returns list of edge dictionaries from the React Flow format
        """
        return self.notation_config.get('edges', []) if self.notation_config else []
    
    @property
    def viewport(self):
        """
        Get viewport settings from notation_config
        
        Returns viewport dictionary with x, y, zoom
        """
        default_viewport = {'x': 0, 'y': 0, 'zoom': 1}
        return self.notation_config.get('viewport', default_viewport) if self.notation_config else default_viewport
    
    @property
    def is_synced_to_falkordb(self):
        """
        Check if diagram has been synced to FalkorDB
        
        Returns True if graph_name is set, False otherwise
        """
        return self.graph_name is not None and self.graph_name != ''
    
    def to_dict(self):
        """
        Convert diagram to dictionary
        
        Useful for API responses and serialization
        """
        return {
            'id': str(self.id),
            'model_id': str(self.model_id),
            'name': self.name,
            'description': self.description,
            'notation': self.notation,
            'graph_name': self.graph_name,
            'notation_config': self.notation_config,
            'visible_concepts': [str(c) for c in self.visible_concepts] if self.visible_concepts else [],
            'settings': self.settings,
            'is_default': self.is_default,
            'validation_errors': self.validation_errors,
            'is_valid': self.is_valid,
            'last_validated_at': self.last_validated_at.isoformat() if self.last_validated_at else None,
            'created_by': str(self.created_by),
            'updated_by': str(self.updated_by) if self.updated_by else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


# ============================================================================
# EXPORTS - Ensure NotationType is exported
# ============================================================================

__all__ = ['Diagram', 'NotationType']