# backend/app/models/__init__.py
"""
Models package - FIXED import order to avoid circular dependencies
Path: backend/app/models/__init__.py

Import order is critical:
1. Base first
2. User (no dependencies)
3. Workspace (depends on User)
4. Folder (depends on User, Workspace)
5. Model (depends on User, Workspace, Folder)
6. Diagram (depends on User, Model)
7. Everything else
"""

# Base must be imported first
from app.db.base import Base

# Import models in dependency order
from app.models.user import User
from app.models.workspace import Workspace
from app.models.folder import Folder
from app.models.model import Model
from app.models.diagram import Diagram
from app.models.layout import Layout
from app.models.version import Version
from app.models.comment import Comment
from app.models.audit_log import AuditLog
from app.models.publish_workflow import PublishWorkflow

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