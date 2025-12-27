# scripts/init_database.py
"""
Database initialization script - FIXED
Creates all tables if they don't exist
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from sqlalchemy import inspect, text
import structlog

from app.db.session import engine, AsyncSessionLocal
from app.db.base import Base
from app.core.security import get_password_hash

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
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("✅ Database tables created successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to create tables: {str(e)}")
        return False


async def create_test_user():
    """Create a test user for development"""
    from sqlalchemy import select
    from app.models.user import User
    
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
                return
            
            # Create test user
            test_user = User(
                email="test@example.com",
                hashed_password=get_password_hash("password123"),
                full_name="Test User",
                is_active=True,
                is_superuser=False
            )
            
            session.add(test_user)
            await session.commit()
            await session.refresh(test_user)
            
            logger.info("✅ Test user created successfully")
            logger.info(f"   Email: test@example.com")
            logger.info(f"   Password: password123")
            logger.info(f"   ID: {test_user.id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to create test user: {str(e)}")
            await session.rollback()
            raise


async def create_sample_workspace():
    """Create a sample workspace for testing"""
    from sqlalchemy import select
    from app.models.workspace import Workspace
    from app.models.user import User
    
    async with AsyncSessionLocal() as session:
        try:
            # Get test user
            result = await session.execute(
                select(User).where(User.email == "test@example.com")
            )
            test_user = result.scalar_one_or_none()
            
            if not test_user:
                logger.warning("⚠️  Test user not found, skipping workspace creation")
                return
            
            # Check if workspace already exists
            result = await session.execute(
                select(Workspace).where(Workspace.name == "My Workspace")
            )
            existing_workspace = result.scalar_one_or_none()
            
            if existing_workspace:
                logger.info("ℹ️  Sample workspace already exists")
                return
            
            # Create sample workspace
            workspace = Workspace(
                name="My Workspace",
                description="Default workspace for testing",
                type="team",
                created_by=str(test_user.id)
            )
            
            session.add(workspace)
            await session.commit()
            await session.refresh(workspace)
            
            logger.info("✅ Sample workspace created")
            logger.info(f"   Name: {workspace.name}")
            logger.info(f"   ID: {workspace.id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to create workspace: {str(e)}")
            await session.rollback()


async def main():
    """Main initialization function"""
    logger.info("=" * 60)
    logger.info("🚀 Database Initialization")
    logger.info("=" * 60)
    
    # Check existing tables
    logger.info("\n1️⃣  Checking existing tables...")
    try:
        existing_tables = await check_tables_exist()
        if existing_tables:
            logger.info(f"   Found {len(existing_tables)} tables:")
            for table in existing_tables:
                logger.info(f"   - {table}")
        else:
            logger.info("   No tables found")
    except Exception as e:
        logger.error(f"   ❌ Error checking tables: {str(e)}")
    
    # Create tables
    logger.info("\n2️⃣  Creating missing tables...")
    success = await create_tables()
    
    if not success:
        logger.error("\n❌ Database initialization failed!")
        return 1
    
    # Check tables again
    logger.info("\n3️⃣  Verifying tables...")
    try:
        tables = await check_tables_exist()
        logger.info(f"   ✅ Database now has {len(tables)} tables")
        for table in tables:
            logger.info(f"   - {table}")
    except Exception as e:
        logger.error(f"   ❌ Error verifying tables: {str(e)}")
    
    # Create test user
    logger.info("\n4️⃣  Creating test user...")
    try:
        await create_test_user()
    except Exception as e:
        logger.error(f"   ❌ Error creating test user: {str(e)}")
    
    # Create sample workspace
    logger.info("\n5️⃣  Creating sample workspace...")
    try:
        await create_sample_workspace()
    except Exception as e:
        logger.error(f"   ❌ Error creating workspace: {str(e)}")
    
    logger.info("\n" + "=" * 60)
    logger.info("✅ Database initialization complete!")
    logger.info("=" * 60)
    logger.info("\nYou can now:")
    logger.info("1. Login with: test@example.com / password123")
    logger.info("2. Or register a new account via the API")
    logger.info("3. API docs available at: http://localhost:8000/docs")
    logger.info("\n")
    
    return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)