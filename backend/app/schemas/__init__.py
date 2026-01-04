# backend/app/schemas/__init__.py
"""
Pydantic schemas for request/response validation
STRATEGIC FIX: Only import schemas that actually exist
"""

# Auth schemas (these exist)
from app.schemas.auth import (
    Token,
    TokenPayload,
    RefreshToken,
    UserRegister,
    UserLogin,
    PasswordReset,
    PasswordResetConfirm,
)

# User schemas (these exist)
from app.schemas.user import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserPasswordUpdate,
    UserResponse,
    UserInDB,
)

# Workspace schemas (these exist)
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

# Folder schemas (these exist)
from app.schemas.folder import (
    FolderBase,
    FolderCreate,
    FolderUpdate,
    FolderMove,
    FolderResponse,
    FolderTree,
    FolderWithModels,
)

# Model schemas (these exist)
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

# Diagram schemas - FIXED: Only import what actually exists in diagram.py
from app.schemas.diagram import (
    DiagramCreate,
    DiagramUpdate,
    DiagramResponse,
    DiagramPublicResponse,
    DiagramListResponse,
    # Removed: DiagramBase, DiagramWithLayouts, DiagramDuplicate (don't exist)
)

# Conditionally import optional schemas if files exist
try:
    from app.schemas.concept import (
        ConceptBase,
        ConceptCreate,
        ConceptUpdate,
        ConceptResponse,
        ConceptWithRelationships,
        ConceptSearch,
    )
except ImportError:
    # Concept schemas don't exist yet - create placeholders
    ConceptBase = None
    ConceptCreate = None
    ConceptUpdate = None
    ConceptResponse = None
    ConceptWithRelationships = None
    ConceptSearch = None

try:
    from app.schemas.relationship import (
        RelationshipBase,
        RelationshipCreate,
        RelationshipUpdate,
        RelationshipResponse,
        RelationshipWithConcepts,
    )
except ImportError:
    # Relationship schemas don't exist yet - create placeholders
    RelationshipBase = None
    RelationshipCreate = None
    RelationshipUpdate = None
    RelationshipResponse = None
    RelationshipWithConcepts = None

try:
    from app.schemas.layout import (
        LayoutEngine,
        LayoutBase,
        LayoutCreate,
        LayoutUpdate,
        LayoutResponse,
        LayoutApply,
        LayoutCompute,
    )
except ImportError:
    # Layout schemas don't exist yet - create placeholders
    LayoutEngine = None
    LayoutBase = None
    LayoutCreate = None
    LayoutUpdate = None
    LayoutResponse = None
    LayoutApply = None
    LayoutCompute = None

try:
    from app.schemas.validation import (
        ValidationSeverity,
        ValidationCategory,
        ValidationMessage,
        ValidationRequest,
        ValidationResponse,
        ValidationRuleConfig,
    )
except ImportError:
    # Validation schemas don't exist yet - skip
    ValidationSeverity = None
    ValidationCategory = None
    ValidationMessage = None
    ValidationRequest = None
    ValidationResponse = None
    ValidationRuleConfig = None

try:
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
except ImportError:
    # Publish schemas don't exist yet - skip
    PublishStatus = None
    PublishRequestBase = None
    PublishRequestCreate = None
    PublishRequestUpdate = None
    PublishRequestResponse = None
    PublishReview = None
    PublishApproval = None
    PublishHistory = None

try:
    from app.schemas.version import (
        VersionBase,
        VersionCreate,
        VersionResponse,
        VersionCompare,
        VersionDiff,
        VersionRestore,
        VersionHistory,
    )
except ImportError:
    # Version schemas don't exist yet - skip
    VersionBase = None
    VersionCreate = None
    VersionResponse = None
    VersionCompare = None
    VersionDiff = None
    VersionRestore = None
    VersionHistory = None

try:
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
except ImportError:
    # Lineage schemas don't exist yet - skip
    LineageDirection = None
    LineageNodeType = None
    LineageNode = None
    LineageEdge = None
    LineageRequest = None
    LineageResponse = None
    ImpactAnalysisRequest = None
    ImpactAnalysisResult = None

try:
    from app.schemas.export import (
        ExportFormat,
        ExportRequest,
        ExportOptions,
        ExportResponse,
        ExportPreview,
    )
except ImportError:
    # Export schemas don't exist yet - skip
    ExportFormat = None
    ExportRequest = None
    ExportOptions = None
    ExportResponse = None
    ExportPreview = None

# Export all successfully imported schemas
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
    # Diagram - Only what exists
    "DiagramCreate",
    "DiagramUpdate",
    "DiagramResponse",
    "DiagramPublicResponse",
    "DiagramListResponse",
]

# Add optional imports if they were successful
if ConceptBase is not None:
    __all__.extend([
        "ConceptBase", "ConceptCreate", "ConceptUpdate", "ConceptResponse",
        "ConceptWithRelationships", "ConceptSearch"
    ])

if RelationshipBase is not None:
    __all__.extend([
        "RelationshipBase", "RelationshipCreate", "RelationshipUpdate",
        "RelationshipResponse", "RelationshipWithConcepts"
    ])

if LayoutEngine is not None:
    __all__.extend([
        "LayoutEngine", "LayoutBase", "LayoutCreate", "LayoutUpdate",
        "LayoutResponse", "LayoutApply", "LayoutCompute"
    ])

if ValidationSeverity is not None:
    __all__.extend([
        "ValidationSeverity", "ValidationCategory", "ValidationMessage",
        "ValidationRequest", "ValidationResponse", "ValidationRuleConfig"
    ])

if PublishStatus is not None:
    __all__.extend([
        "PublishStatus", "PublishRequestBase", "PublishRequestCreate",
        "PublishRequestUpdate", "PublishRequestResponse", "PublishReview",
        "PublishApproval", "PublishHistory"
    ])

if VersionBase is not None:
    __all__.extend([
        "VersionBase", "VersionCreate", "VersionResponse", "VersionCompare",
        "VersionDiff", "VersionRestore", "VersionHistory"
    ])

if LineageDirection is not None:
    __all__.extend([
        "LineageDirection", "LineageNodeType", "LineageNode", "LineageEdge",
        "LineageRequest", "LineageResponse", "ImpactAnalysisRequest",
        "ImpactAnalysisResult"
    ])

if ExportFormat is not None:
    __all__.extend([
        "ExportFormat", "ExportRequest", "ExportOptions", "ExportResponse",
        "ExportPreview"
    ])