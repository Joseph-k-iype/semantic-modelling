# backend/app/models/__init__.py
"""
Models Package - FIXED: Removed NotationType import
Path: backend/app/models/__init__.py
"""

# User models
from app.models.user import User, UserRole

# Workspace models
from app.models.workspace import (
    Workspace,
    WorkspaceType,
    WorkspaceMember,
    WorkspaceRole,
    WorkspaceInvitation,
    InvitationStatus
)

# Folder model
from app.models.folder import Folder

# Model models
from app.models.model import Model, ModelType, ModelStatus, ModelStatistics, ModelTag

# Diagram model - FIXED: Removed NotationType (it doesn't exist in diagram.py)
from app.models.diagram import Diagram

# Layout models
from app.models.layout import Layout, LayoutType, LayoutSnapshot

# Version model
from app.models.version import Version

# Comment models
from app.models.comment import (
    Comment,
    EntityType,
    CommentMention,
    CommentReaction
)

# Publish workflow model
from app.models.publish_workflow import PublishWorkflow, PublishWorkflowStatus

# Audit log model
from app.models.audit_log import AuditLog, AuditLogAction

# Export all models for easy access
__all__ = [
    # User
    "User",
    "UserRole",
    # Workspace
    "Workspace",
    "WorkspaceType",
    "WorkspaceMember",
    "WorkspaceRole",
    "WorkspaceInvitation",
    "InvitationStatus",
    # Folder
    "Folder",
    # Model
    "Model",
    "ModelType",
    "ModelStatus",
    "ModelStatistics",
    "ModelTag",
    # Diagram - FIXED: Removed NotationType from exports
    "Diagram",
    # Layout
    "Layout",
    "LayoutType",
    "LayoutSnapshot",
    # Version
    "Version",
    # Comment
    "Comment",
    "EntityType",
    "CommentMention",
    "CommentReaction",
    # Publish Workflow
    "PublishWorkflow",
    "PublishWorkflowStatus",
    # Audit Log
    "AuditLog",
    "AuditLogAction",
]