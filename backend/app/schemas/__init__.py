"""
Pydantic schemas for request/response validation
"""

from app.schemas.auth import (
    Token,
    TokenPayload,
    RefreshToken,
    UserRegister,
    UserLogin,
    PasswordReset,
    PasswordResetConfirm,
)
from app.schemas.user import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserPasswordUpdate,
    UserResponse,
    UserInDB,
)
from app.schemas.workspace import (
    WorkspaceType,
    WorkspaceBase,
    WorkspaceCreate,
    WorkspaceUpdate,
    WorkspaceResponse,
    WorkspaceMemberRole,
    WorkspaceMemberBase,
    WorkspaceMemberCreate,
    WorkspaceMemberUpdate,
    WorkspaceMemberResponse,
    WorkspaceWithMembers,
)
from app.schemas.folder import (
    FolderBase,
    FolderCreate,
    FolderUpdate,
    FolderMove,
    FolderResponse,
    FolderTree,
    FolderWithModels,
)
from app.schemas.model import (
    ModelType,
    ModelStatus,
    ModelBase,
    ModelCreate,
    ModelUpdate,
    ModelResponse,
    ModelWithStats,
    ModelMove,
    ModelDuplicate,
)
from app.schemas.diagram import (
    DiagramBase,
    DiagramCreate,
    DiagramUpdate,
    DiagramResponse,
    DiagramWithLayouts,
    DiagramDuplicate,
)
from app.schemas.concept import (
    ConceptBase,
    ConceptCreate,
    ConceptUpdate,
    ConceptResponse,
    ConceptWithRelationships,
    ConceptSearch,
)
from app.schemas.relationship import (
    RelationshipBase,
    RelationshipCreate,
    RelationshipUpdate,
    RelationshipResponse,
    RelationshipWithConcepts,
)
from app.schemas.layout import (
    LayoutEngine,
    LayoutBase,
    LayoutCreate,
    LayoutUpdate,
    LayoutResponse,
    LayoutApply,
    LayoutCompute,
)
from app.schemas.validation import (
    ValidationSeverity,
    ValidationCategory,
    ValidationMessage,
    ValidationRequest,
    ValidationResponse,
    ValidationRuleConfig,
)
from app.schemas.publish import (
    PublishStatus,
    PublishRequestBase,
    PublishRequestCreate,
    PublishRequestUpdate,
    PublishRequestResponse,
    PublishReview,
    PublishApproval,
    PublishHistory,
)
from app.schemas.version import (
    VersionBase,
    VersionCreate,
    VersionResponse,
    VersionCompare,
    VersionDiff,
    VersionRestore,
    VersionHistory,
)
from app.schemas.lineage import (
    LineageDirection,
    LineageNodeType,
    LineageNode,
    LineageEdge,
    LineageRequest,
    LineageResponse,
    ImpactAnalysisRequest,
    ImpactAnalysisResult,
)
from app.schemas.export import (
    ExportFormat,
    ExportRequest,
    ExportOptions,
    ExportResponse,
    ExportPreview,
)

__all__ = [
    # Auth
    "Token",
    "TokenPayload",
    "RefreshToken",
    "UserRegister",
    "UserLogin",
    "PasswordReset",
    "PasswordResetConfirm",
    # User
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserPasswordUpdate",
    "UserResponse",
    "UserInDB",
    # Workspace
    "WorkspaceType",
    "WorkspaceBase",
    "WorkspaceCreate",
    "WorkspaceUpdate",
    "WorkspaceResponse",
    "WorkspaceMemberRole",
    "WorkspaceMemberBase",
    "WorkspaceMemberCreate",
    "WorkspaceMemberUpdate",
    "WorkspaceMemberResponse",
    "WorkspaceWithMembers",
    # Folder
    "FolderBase",
    "FolderCreate",
    "FolderUpdate",
    "FolderMove",
    "FolderResponse",
    "FolderTree",
    "FolderWithModels",
    # Model
    "ModelType",
    "ModelStatus",
    "ModelBase",
    "ModelCreate",
    "ModelUpdate",
    "ModelResponse",
    "ModelWithStats",
    "ModelMove",
    "ModelDuplicate",
    # Diagram
    "DiagramBase",
    "DiagramCreate",
    "DiagramUpdate",
    "DiagramResponse",
    "DiagramWithLayouts",
    "DiagramDuplicate",
    # Concept
    "ConceptBase",
    "ConceptCreate",
    "ConceptUpdate",
    "ConceptResponse",
    "ConceptWithRelationships",
    "ConceptSearch",
    # Relationship
    "RelationshipBase",
    "RelationshipCreate",
    "RelationshipUpdate",
    "RelationshipResponse",
    "RelationshipWithConcepts",
    # Layout
    "LayoutEngine",
    "LayoutBase",
    "LayoutCreate",
    "LayoutUpdate",
    "LayoutResponse",
    "LayoutApply",
    "LayoutCompute",
    # Validation
    "ValidationSeverity",
    "ValidationCategory",
    "ValidationMessage",
    "ValidationRequest",
    "ValidationResponse",
    "ValidationRuleConfig",
    # Publish
    "PublishStatus",
    "PublishRequestBase",
    "PublishRequestCreate",
    "PublishRequestUpdate",
    "PublishRequestResponse",
    "PublishReview",
    "PublishApproval",
    "PublishHistory",
    # Version
    "VersionBase",
    "VersionCreate",
    "VersionResponse",
    "VersionCompare",
    "VersionDiff",
    "VersionRestore",
    "VersionHistory",
    # Lineage
    "LineageDirection",
    "LineageNodeType",
    "LineageNode",
    "LineageEdge",
    "LineageRequest",
    "LineageResponse",
    "ImpactAnalysisRequest",
    "ImpactAnalysisResult",
    # Export
    "ExportFormat",
    "ExportRequest",
    "ExportOptions",
    "ExportResponse",
    "ExportPreview",
]