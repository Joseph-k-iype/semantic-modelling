# backend/app/api/deps.py
"""
API Dependencies - COMPLETE with all workspace access logic implemented
Path: backend/app/api/deps.py

Provides dependency injection for:
- Database sessions
- Current authenticated user
- Permission checks
- Workspace access verification
"""

from typing import Optional, AsyncGenerator
from uuid import UUID
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import structlog

from app.db.session import AsyncSessionLocal
from app.models.user import User, UserRole
from app.core.security import verify_token

logger = structlog.get_logger(__name__)

# HTTP Bearer token authentication scheme
security = HTTPBearer(auto_error=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session
    
    Yields:
        AsyncSession: Database session
        
    Note:
        Session is automatically closed after request
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Dependency to get current authenticated user from JWT token
    
    Args:
        credentials: HTTP Bearer token from Authorization header
        db: Database session
        
    Returns:
        Current authenticated user
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    # Check if credentials were provided
    if not credentials:
        logger.warning("auth_failed", reason="no_credentials")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract token from credentials
    token = credentials.credentials
    
    # Verify token and extract user ID
    user_id = verify_token(token, token_type="access")
    
    if not user_id:
        logger.warning("auth_failed", reason="invalid_token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    try:
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            logger.warning(
                "auth_failed",
                reason="user_not_found",
                user_id=user_id
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check if user is active
        if not user.is_active:
            logger.warning(
                "auth_failed",
                reason="inactive_user",
                user_id=user_id
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Inactive user",
            )
        
        return user
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(
            "auth_error",
            error=str(e),
            user_id=user_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication error",
        )


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependency to get current active user
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Current user (guaranteed to be active)
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependency to get current admin user
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Current user (guaranteed to be admin)
        
    Raises:
        HTTPException: If user is not an admin
    """
    if current_user.role != UserRole.ADMIN:
        logger.warning(
            "permission_denied",
            user_id=str(current_user.id),
            required_role="ADMIN",
            actual_role=current_user.role.value
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[str]:
    """
    Dependency to optionally get current user ID from token
    
    This is useful for endpoints that can work both with and without authentication
    
    Args:
        credentials: HTTP Bearer token from Authorization header
        
    Returns:
        User ID if authenticated, None otherwise
    """
    if not credentials:
        return None
    
    token = credentials.credentials
    user_id = verify_token(token, token_type="access")
    
    return user_id


async def verify_workspace_access(
    workspace_id: str,
    required_role: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> bool:
    """
    Verify that current user has access to a workspace
    
    Args:
        workspace_id: Workspace ID to check
        required_role: Required role in workspace (VIEWER, EDITOR, PUBLISHER, ADMIN)
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        True if user has access
        
    Raises:
        HTTPException: If user doesn't have access or insufficient permissions
    """
    from app.models.workspace import Workspace, WorkspaceMember
    
    try:
        # Convert string to UUID if needed
        if isinstance(workspace_id, str):
            workspace_uuid = UUID(workspace_id)
        else:
            workspace_uuid = workspace_id
        
        # System admins have access to everything
        if current_user.role == UserRole.ADMIN:
            logger.info(
                "workspace_access_granted",
                user_id=str(current_user.id),
                workspace_id=str(workspace_uuid),
                reason="admin_user"
            )
            return True
        
        # Check if workspace exists
        result = await db.execute(
            select(Workspace).where(
                and_(
                    Workspace.id == workspace_uuid,
                    Workspace.deleted_at.is_(None)
                )
            )
        )
        workspace = result.scalar_one_or_none()
        
        if not workspace:
            logger.warning(
                "workspace_not_found",
                workspace_id=str(workspace_uuid)
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace not found"
            )
        
        # Check if user is the workspace owner
        if workspace.owner_id == current_user.id:
            logger.info(
                "workspace_access_granted",
                user_id=str(current_user.id),
                workspace_id=str(workspace_uuid),
                reason="owner"
            )
            return True
        
        # Check workspace membership
        result = await db.execute(
            select(WorkspaceMember).where(
                and_(
                    WorkspaceMember.workspace_id == workspace_uuid,
                    WorkspaceMember.user_id == current_user.id,
                    WorkspaceMember.deleted_at.is_(None)
                )
            )
        )
        member = result.scalar_one_or_none()
        
        if not member:
            logger.warning(
                "workspace_access_denied",
                user_id=str(current_user.id),
                workspace_id=str(workspace_uuid),
                reason="not_a_member"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this workspace"
            )
        
        # Check if specific role is required
        if required_role:
            role_hierarchy = {
                "VIEWER": 1,
                "EDITOR": 2,
                "PUBLISHER": 3,
                "ADMIN": 4
            }
            
            member_role_level = role_hierarchy.get(member.role.value, 0)
            required_role_level = role_hierarchy.get(required_role, 0)
            
            if member_role_level < required_role_level:
                logger.warning(
                    "workspace_permission_denied",
                    user_id=str(current_user.id),
                    workspace_id=str(workspace_uuid),
                    member_role=member.role.value,
                    required_role=required_role
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions. {required_role} role required."
                )
        
        logger.info(
            "workspace_access_granted",
            user_id=str(current_user.id),
            workspace_id=str(workspace_uuid),
            role=member.role.value
        )
        
        return True
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(
            "invalid_workspace_id",
            workspace_id=workspace_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid workspace ID format"
        )
    except Exception as e:
        logger.error(
            "workspace_access_error",
            error=str(e),
            workspace_id=workspace_id,
            user_id=str(current_user.id)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error verifying workspace access"
        )


async def verify_model_access(
    model_id: str,
    required_workspace_role: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> bool:
    """
    Verify that current user has access to a model
    
    Access is granted if user has access to the model's workspace
    
    Args:
        model_id: Model ID to check
        required_workspace_role: Required role in workspace
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        True if user has access
        
    Raises:
        HTTPException: If user doesn't have access
    """
    from app.models.model import Model
    
    try:
        # Convert string to UUID if needed
        if isinstance(model_id, str):
            model_uuid = UUID(model_id)
        else:
            model_uuid = model_id
        
        # Get model to find workspace
        result = await db.execute(
            select(Model).where(
                and_(
                    Model.id == model_uuid,
                    Model.deleted_at.is_(None)
                )
            )
        )
        model = result.scalar_one_or_none()
        
        if not model:
            logger.warning(
                "model_not_found",
                model_id=str(model_uuid)
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Model not found"
            )
        
        # Verify access to model's workspace
        return await verify_workspace_access(
            workspace_id=str(model.workspace_id),
            required_role=required_workspace_role,
            current_user=current_user,
            db=db
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(
            "invalid_model_id",
            model_id=model_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid model ID format"
        )
    except Exception as e:
        logger.error(
            "model_access_error",
            error=str(e),
            model_id=model_id,
            user_id=str(current_user.id)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error verifying model access"
        )


async def verify_diagram_access(
    diagram_id: str,
    required_workspace_role: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> bool:
    """
    Verify that current user has access to a diagram
    
    Access is granted if user has access to the diagram's model's workspace
    
    Args:
        diagram_id: Diagram ID to check
        required_workspace_role: Required role in workspace
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        True if user has access
        
    Raises:
        HTTPException: If user doesn't have access
    """
    from app.models.diagram import Diagram
    
    try:
        # Convert string to UUID if needed
        if isinstance(diagram_id, str):
            diagram_uuid = UUID(diagram_id)
        else:
            diagram_uuid = diagram_id
        
        # Get diagram to find model
        result = await db.execute(
            select(Diagram).where(
                and_(
                    Diagram.id == diagram_uuid,
                    Diagram.deleted_at.is_(None)
                )
            )
        )
        diagram = result.scalar_one_or_none()
        
        if not diagram:
            logger.warning(
                "diagram_not_found",
                diagram_id=str(diagram_uuid)
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Diagram not found"
            )
        
        # Verify access to diagram's model
        return await verify_model_access(
            model_id=str(diagram.model_id),
            required_workspace_role=required_workspace_role,
            current_user=current_user,
            db=db
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(
            "invalid_diagram_id",
            diagram_id=diagram_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid diagram ID format"
        )
    except Exception as e:
        logger.error(
            "diagram_access_error",
            error=str(e),
            diagram_id=diagram_id,
            user_id=str(current_user.id)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error verifying diagram access"
        )


async def get_user_workspace_role(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> str:
    """
    Get user's role in a specific workspace
    
    Args:
        workspace_id: Workspace ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        User's role in workspace (VIEWER, EDITOR, PUBLISHER, ADMIN, or OWNER)
        
    Raises:
        HTTPException: If user doesn't have access to workspace
    """
    from app.models.workspace import Workspace, WorkspaceMember
    
    try:
        # Convert string to UUID if needed
        if isinstance(workspace_id, str):
            workspace_uuid = UUID(workspace_id)
        else:
            workspace_uuid = workspace_id
        
        # System admins are treated as ADMIN in all workspaces
        if current_user.role == UserRole.ADMIN:
            return "ADMIN"
        
        # Get workspace
        result = await db.execute(
            select(Workspace).where(
                and_(
                    Workspace.id == workspace_uuid,
                    Workspace.deleted_at.is_(None)
                )
            )
        )
        workspace = result.scalar_one_or_none()
        
        if not workspace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace not found"
            )
        
        # Check if user is owner
        if workspace.owner_id == current_user.id:
            return "OWNER"
        
        # Get membership
        result = await db.execute(
            select(WorkspaceMember).where(
                and_(
                    WorkspaceMember.workspace_id == workspace_uuid,
                    WorkspaceMember.user_id == current_user.id,
                    WorkspaceMember.deleted_at.is_(None)
                )
            )
        )
        member = result.scalar_one_or_none()
        
        if not member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this workspace"
            )
        
        return member.role.value
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "get_workspace_role_error",
            error=str(e),
            workspace_id=workspace_id,
            user_id=str(current_user.id)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting workspace role"
        )


class PermissionChecker:
    """
    Reusable permission checker class for various resource types
    """
    
    def __init__(self, resource_type: str, required_role: Optional[str] = None):
        """
        Initialize permission checker
        
        Args:
            resource_type: Type of resource (workspace, model, diagram)
            required_role: Required workspace role
        """
        self.resource_type = resource_type
        self.required_role = required_role
    
    async def __call__(
        self,
        resource_id: str,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> bool:
        """
        Check permissions for resource
        
        Args:
            resource_id: Resource ID
            current_user: Current authenticated user
            db: Database session
            
        Returns:
            True if user has access
        """
        if self.resource_type == "workspace":
            return await verify_workspace_access(
                workspace_id=resource_id,
                required_role=self.required_role,
                current_user=current_user,
                db=db
            )
        elif self.resource_type == "model":
            return await verify_model_access(
                model_id=resource_id,
                required_workspace_role=self.required_role,
                current_user=current_user,
                db=db
            )
        elif self.resource_type == "diagram":
            return await verify_diagram_access(
                diagram_id=resource_id,
                required_workspace_role=self.required_role,
                current_user=current_user,
                db=db
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown resource type: {self.resource_type}"
            )


# Convenience permission checkers for common use cases
require_workspace_viewer = PermissionChecker("workspace", "VIEWER")
require_workspace_editor = PermissionChecker("workspace", "EDITOR")
require_workspace_publisher = PermissionChecker("workspace", "PUBLISHER")
require_workspace_admin = PermissionChecker("workspace", "ADMIN")

require_model_viewer = PermissionChecker("model", "VIEWER")
require_model_editor = PermissionChecker("model", "EDITOR")
require_model_publisher = PermissionChecker("model", "PUBLISHER")

require_diagram_viewer = PermissionChecker("diagram", "VIEWER")
require_diagram_editor = PermissionChecker("diagram", "EDITOR")
require_diagram_publisher = PermissionChecker("diagram", "PUBLISHER")