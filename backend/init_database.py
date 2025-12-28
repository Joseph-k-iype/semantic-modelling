# backend/init_database.py
"""
Database initialization script - COMPLETE FIX
Creates all tables if they don't exist and handles proper model imports
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import inspect
import structlog

from app.db.session import engine, AsyncSessionLocal
from app.db.base import Base
from app.core.security import get_password_hash

# CRITICAL: Import ALL models before creating tables
# This ensures SQLAlchemy knows about all models and their relationships
from app.models.user import User
from app.models.workspace import Workspace
from app.models.folder import Folder
from app.models.model import Model
from app.models.diagram import Diagram
from app.models.version import Version
from app.models.audit_log import AuditLog
from app.models.layout import Layout
from app.models.publish_workflow import PublishWorkflow
from app.models.comment import Comment

logger = structlog.get_logger()


async def check_tables_exist():
    """Check if database tables exist"""
    async with engine.begin() as conn:
        # Get list of existing tables
        result = await conn.run_sync(
            lambda sync_conn: inspect(sync_conn).get_table_names()
        )
        return result


async def create_tables():
    """Create all database tables"""
    logger.info("Creating database tables...")
    
    try:
        async with engine.begin() as conn:
            # Drop all tables first (for development/testing)
            # Comment this out in production!
            await conn.run_sync(Base.metadata.drop_all)
            logger.info("  Dropped existing tables...")
            
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("✅ Database tables created successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to create tables: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def create_test_user():
    """Create a test user for development"""
    from sqlalchemy import select
    
    async with AsyncSessionLocal() as session:
        try:
            # Check if test user already exists
            result = await session.execute(
                select(User).where(User.email == "test@example.com")
            )
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                logger.info("ℹ️  Test user already exists")
                logger.info(f"   Email: test@example.com")
                logger.info(f"   ID: {existing_user.id}")
                return existing_user
            
            # Create test user
            test_user = User(
                email="test@example.com",
                username="testuser",  # FIXED: Include username
                hashed_password=get_password_hash("password123"),
                full_name="Test User",
                is_active=True,
                is_superuser=False,
                is_verified=True
            )
            
            session.add(test_user)
            await session.commit()
            await session.refresh(test_user)
            
            logger.info("✅ Test user created successfully")
            logger.info(f"   Email: test@example.com")
            logger.info(f"   Username: testuser")
            logger.info(f"   Password: password123")
            logger.info(f"   ID: {test_user.id}")
            
            return test_user
            
        except Exception as e:
            logger.error(f"❌ Failed to create test user: {str(e)}")
            import traceback
            traceback.print_exc()
            await session.rollback()
            raise


async def create_sample_workspace(test_user):
    """Create a sample workspace for testing"""
    from sqlalchemy import select
    
    async with AsyncSessionLocal() as session:
        try:
            # Check if workspace already exists
            result = await session.execute(
                select(Workspace).where(Workspace.name == "My First Workspace")
            )
            existing_workspace = result.scalar_one_or_none()
            
            if existing_workspace:
                logger.info("ℹ️  Sample workspace already exists")
                logger.info(f"   Name: My First Workspace")
                logger.info(f"   ID: {existing_workspace.id}")
                return existing_workspace
            
            # Create workspace
            workspace = Workspace(
                name="My First Workspace",
                description="A sample workspace for testing",
                type="personal",
                created_by=test_user.id
            )
            
            session.add(workspace)
            await session.commit()
            await session.refresh(workspace)
            
            logger.info("✅ Sample workspace created successfully")
            logger.info(f"   Name: My First Workspace")
            logger.info(f"   ID: {workspace.id}")
            
            return workspace
            
        except Exception as e:
            logger.error(f"❌ Failed to create workspace: {str(e)}")
            import traceback
            traceback.print_exc()
            await session.rollback()
            raise


async def create_sample_model(test_user, workspace):
    """Create a sample model for testing"""
    from sqlalchemy import select
    
    async with AsyncSessionLocal() as session:
        try:
            # Check if model already exists
            result = await session.execute(
                select(Model).where(
                    Model.name == "Sample ER Model",
                    Model.workspace_id == workspace.id
                )
            )
            existing_model = result.scalar_one_or_none()
            
            if existing_model:
                logger.info("ℹ️  Sample model already exists")
                logger.info(f"   Name: Sample ER Model")
                logger.info(f"   ID: {existing_model.id}")
                return existing_model
            
            # Create model
            model = Model(
                name="Sample ER Model",
                description="A sample ER model for testing",
                type="ER",
                workspace_id=workspace.id,
                created_by=test_user.id,
                updated_by=test_user.id
            )
            
            session.add(model)
            await session.commit()
            await session.refresh(model)
            
            logger.info("✅ Sample model created successfully")
            logger.info(f"   Name: Sample ER Model")
            logger.info(f"   ID: {model.id}")
            
            return model
            
        except Exception as e:
            logger.error(f"❌ Failed to create model: {str(e)}")
            import traceback
            traceback.print_exc()
            await session.rollback()
            raise


async def main():
    """Main initialization function"""
    logger.info("============================================================")
    logger.info("🚀 Database Initialization")
    logger.info("============================================================")
    
    # Step 1: Check existing tables
    logger.info("\n1️⃣  Checking existing tables...")
    existing_tables = await check_tables_exist()
    if existing_tables:
        logger.info(f"   Found {len(existing_tables)} tables:")
        for table in existing_tables:
            logger.info(f"   - {table}")
    else:
        logger.info("   No tables found")
    
    # Step 2: Create tables
    logger.info("\n2️⃣  Creating missing tables...")
    success = await create_tables()
    if not success:
        logger.error("❌ Failed to create tables. Exiting.")
        return
    
    # Step 3: Verify tables
    logger.info("\n3️⃣  Verifying tables...")
    new_tables = await check_tables_exist()
    logger.info(f"   ✅ Database now has {len(new_tables)} tables")
    for table in sorted(new_tables):
        logger.info(f"   - {table}")
    
    # Step 4: Create test user
    logger.info("\n4️⃣  Creating test user...")
    try:
        test_user = await create_test_user()
    except Exception as e:
        logger.error(f"❌ Error creating test user: {str(e)}")
        test_user = None
    
    # Step 5: Create sample workspace
    if test_user:
        logger.info("\n5️⃣  Creating sample workspace...")
        try:
            workspace = await create_sample_workspace(test_user)
        except Exception as e:
            logger.error(f"❌ Error creating workspace: {str(e)}")
            workspace = None
    else:
        workspace = None
        logger.warning("⚠️  Skipping workspace creation (no test user)")
    
    # Step 6: Create sample model
    if test_user and workspace:
        logger.info("\n6️⃣  Creating sample model...")
        try:
            model = await create_sample_model(test_user, workspace)
        except Exception as e:
            logger.error(f"❌ Error creating model: {str(e)}")
    else:
        logger.warning("⚠️  Skipping model creation (no test user or workspace)")
    
    # Summary
    logger.info("\n============================================================")
    logger.info("✅ Database initialization complete!")
    logger.info("============================================================")
    logger.info("\nYou can now:")
    logger.info("1. Login with: test@example.com / password123")
    logger.info("2. Or register a new account via the API")
    logger.info("3. API docs available at: http://localhost:8000/docs")
    logger.info("")


if __name__ == "__main__":
    asyncio.run(main())