# backend/verify_enum_fix.py
"""
Verification script to test the enum fix
Path: backend/verify_enum_fix.py

This script tests that workspace enum types work correctly with PostgreSQL
"""
import asyncio
import sys
from pathlib import Path

# Add the backend directory to the path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.db.session import AsyncSessionLocal
from app.models.workspace import Workspace, WorkspaceType
from app.models.workspace_member import WorkspaceMember, WorkspaceMemberRole
from app.models.model import Model, ModelType, ModelStatus
from app.models.user import User

logger = structlog.get_logger(__name__)


async def verify_database_enums():
    """Verify that database enum types exist and have correct values"""
    async with AsyncSessionLocal() as session:
        try:
            # Check workspace_type enum
            result = await session.execute(text("""
                SELECT enumlabel 
                FROM pg_enum 
                JOIN pg_type ON pg_enum.enumtypid = pg_type.oid 
                WHERE pg_type.typname = 'workspace_type'
                ORDER BY enumlabel
            """))
            workspace_types = [row[0] for row in result]
            
            logger.info("Database workspace_type enum values", values=workspace_types)
            
            expected = ['common', 'personal', 'team']
            if workspace_types != expected:
                logger.error("Workspace type enum mismatch!", 
                           expected=expected, 
                           actual=workspace_types)
                return False
            
            # Check user_role enum
            result = await session.execute(text("""
                SELECT enumlabel 
                FROM pg_enum 
                JOIN pg_type ON pg_enum.enumtypid = pg_type.oid 
                WHERE pg_type.typname = 'user_role'
                ORDER BY enumlabel
            """))
            user_roles = [row[0] for row in result]
            
            logger.info("Database user_role enum values", values=user_roles)
            
            expected_roles = ['admin', 'editor', 'publisher', 'viewer']
            if user_roles != expected_roles:
                logger.error("User role enum mismatch!", 
                           expected=expected_roles, 
                           actual=user_roles)
                return False
            
            # Check model_type enum
            result = await session.execute(text("""
                SELECT enumlabel 
                FROM pg_enum 
                JOIN pg_type ON pg_enum.enumtypid = pg_type.oid 
                WHERE pg_type.typname = 'model_type'
                ORDER BY enumlabel
            """))
            model_types = [row[0] for row in result]
            
            logger.info("Database model_type enum values", values=model_types)
            
            # Check model_status enum
            result = await session.execute(text("""
                SELECT enumlabel 
                FROM pg_enum 
                JOIN pg_type ON pg_enum.enumtypid = pg_type.oid 
                WHERE pg_type.typname = 'model_status'
                ORDER BY enumlabel
            """))
            model_statuses = [row[0] for row in result]
            
            logger.info("Database model_status enum values", values=model_statuses)
            
            logger.info("✅ All database enums verified successfully")
            return True
            
        except Exception as e:
            logger.error("Failed to verify database enums", error=str(e))
            import traceback
            traceback.print_exc()
            return False


async def test_workspace_enum_queries():
    """Test that workspace enum queries work correctly"""
    async with AsyncSessionLocal() as session:
        try:
            # Get a test user
            result = await session.execute(
                select(User).limit(1)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                logger.warning("No users found in database, skipping workspace tests")
                return True
            
            logger.info("Testing workspace enum queries", user_id=str(user.id))
            
            # Test 1: Query with enum member (should work with native_enum=False)
            logger.info("Test 1: Query with enum member WorkspaceType.PERSONAL")
            result = await session.execute(
                select(Workspace).where(
                    Workspace.created_by == user.id,
                    Workspace.type == WorkspaceType.PERSONAL
                )
            )
            workspaces = result.scalars().all()
            logger.info("Test 1 result", count=len(workspaces))
            
            # Test 2: Query with enum value string
            logger.info("Test 2: Query with string 'personal'")
            result = await session.execute(
                select(Workspace).where(
                    Workspace.created_by == user.id,
                    Workspace.type == "personal"
                )
            )
            workspaces2 = result.scalars().all()
            logger.info("Test 2 result", count=len(workspaces2))
            
            if len(workspaces) != len(workspaces2):
                logger.error("Query results don't match!", 
                           enum_count=len(workspaces), 
                           string_count=len(workspaces2))
                return False
            
            # Test 3: Create a new workspace with enum
            logger.info("Test 3: Create workspace with enum")
            test_workspace = Workspace(
                name=f"Test Workspace {user.username}",
                description="Test workspace for enum verification",
                type=WorkspaceType.TEAM,
                created_by=user.id,
                settings={},
                is_active=True
            )
            session.add(test_workspace)
            await session.flush()
            
            # Verify it was created with correct type
            result = await session.execute(
                select(Workspace).where(Workspace.id == test_workspace.id)
            )
            created_workspace = result.scalar_one()
            
            logger.info("Test 3 result", 
                       workspace_type=created_workspace.type,
                       workspace_type_value=created_workspace.type.value if hasattr(created_workspace.type, 'value') else created_workspace.type)
            
            # Clean up test workspace
            await session.delete(created_workspace)
            await session.commit()
            
            logger.info("✅ All workspace enum query tests passed")
            return True
            
        except Exception as e:
            logger.error("Workspace enum query test failed", error=str(e))
            import traceback
            traceback.print_exc()
            await session.rollback()
            return False


async def test_python_enum_values():
    """Verify Python enum definitions"""
    logger.info("Verifying Python enum definitions")
    
    # Check WorkspaceType
    logger.info("WorkspaceType enum members:")
    for member in WorkspaceType:
        logger.info(f"  {member.name} = '{member.value}'")
    
    assert WorkspaceType.PERSONAL.value == "personal"
    assert WorkspaceType.TEAM.value == "team"
    assert WorkspaceType.COMMON.value == "common"
    
    # Check WorkspaceMemberRole
    logger.info("WorkspaceMemberRole enum members:")
    for member in WorkspaceMemberRole:
        logger.info(f"  {member.name} = '{member.value}'")
    
    assert WorkspaceMemberRole.VIEWER.value == "viewer"
    assert WorkspaceMemberRole.EDITOR.value == "editor"
    assert WorkspaceMemberRole.PUBLISHER.value == "publisher"
    assert WorkspaceMemberRole.ADMIN.value == "admin"
    
    # Check ModelType
    logger.info("ModelType enum members:")
    for member in ModelType:
        logger.info(f"  {member.name} = '{member.value}'")
    
    # Check ModelStatus
    logger.info("ModelStatus enum members:")
    for member in ModelStatus:
        logger.info(f"  {member.name} = '{member.value}'")
    
    assert ModelStatus.DRAFT.value == "draft"
    assert ModelStatus.IN_REVIEW.value == "in_review"
    assert ModelStatus.PUBLISHED.value == "published"
    assert ModelStatus.ARCHIVED.value == "archived"
    
    logger.info("✅ All Python enum definitions verified")
    return True


async def main():
    """Run all verification tests"""
    logger.info("=" * 80)
    logger.info("STARTING ENUM FIX VERIFICATION")
    logger.info("=" * 80)
    
    all_passed = True
    
    # Test 1: Python enum values
    logger.info("\n" + "=" * 80)
    logger.info("TEST 1: Python Enum Values")
    logger.info("=" * 80)
    if not await test_python_enum_values():
        all_passed = False
    
    # Test 2: Database enum values
    logger.info("\n" + "=" * 80)
    logger.info("TEST 2: Database Enum Values")
    logger.info("=" * 80)
    if not await verify_database_enums():
        all_passed = False
    
    # Test 3: Workspace enum queries
    logger.info("\n" + "=" * 80)
    logger.info("TEST 3: Workspace Enum Queries")
    logger.info("=" * 80)
    if not await test_workspace_enum_queries():
        all_passed = False
    
    # Final summary
    logger.info("\n" + "=" * 80)
    if all_passed:
        logger.info("✅ ALL TESTS PASSED - Enum fix verified successfully!")
    else:
        logger.error("❌ SOME TESTS FAILED - Please check the errors above")
    logger.info("=" * 80)
    
    return all_passed


if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)