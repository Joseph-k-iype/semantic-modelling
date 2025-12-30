# backend/app/models/__init__.py
"""
Models package - Centralizes all model imports
Path: backend/app/models/__init__.py

Import order is critical to avoid circular dependencies:
1. Import Base first (from db.base)
2. Import models in dependency order (User has no deps, others depend on User, etc.)

IMPORTANT: Base is defined in app/db/base.py
Models import Base from there and define their tables.
This file imports all models to register them with SQLAlchemy.
"""

# Step 1: Import Base (this should never cause issues since base.py is clean)
from app.db.base import Base

# Step 2: Import models in dependency order
# User - no foreign key dependencies
from app.models.user import User

# Workspace - depends on User (owner_id)
from app.models.workspace import Workspace

# Folder - depends on User and Workspace
from app.models.folder import Folder

# Model - depends on User, Workspace, Folder
from app.models.model import Model

# Diagram - depends on User and Model
from app.models.diagram import Diagram

# Layout - depends on User and Diagram
from app.models.layout import Layout

# Version - depends on User and Model
from app.models.version import Version

# Comment - depends on User, Model, Diagram
from app.models.comment import Comment

# AuditLog - depends on User and Workspace
from app.models.audit_log import AuditLog

# PublishWorkflow - depends on User and Workspace
from app.models.publish_workflow import PublishWorkflow

# Export all models for easy importing
__all__ = [
    "Base",
    "User",
    "Workspace",
    "Folder",
    "Model",
    "Diagram",
    "Layout",
    "Version",
    "Comment",
    "AuditLog",
    "PublishWorkflow",
]