# backend/init_database.py
"""
Database Initialization Script - FIXED with proper ENUM handling
Path: backend/init_database.py
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import structlog
import uuid

from app.core.config import settings
from app.db.base import Base
from app.models.user import User, UserRole
from app.models.workspace import Workspace, WorkspaceType
from app.models.model import Model, ModelType, ModelStatus
from app.core.security import get_password_hash

logger = structlog.get_logger(__name__)


async def verify_connection(engine):
    """Verify database connection"""
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("✅ Database connection successful")
        return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False


async def get_table_count(engine):
    """Get list of existing tables"""
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result.fetchall()]
        return tables
    except Exception as e:
        logger.error(f"❌ Failed to get tables: {e}")
        return []


async def create_tables(engine):
    """Create all tables"""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ All tables created successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to create tables: {e}")
        return False


async def create_test_user(session: AsyncSession) -> User:
    """Create test user - FIXED to use UserRole enum"""
    try:
        result = await session.execute(
            select(User).where(User.email == "test@example.com")
        )
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            logger.info("Test user already exists")
            logger.info(f"   Email: {existing_user.email}")
            return existing_user
        
        # CRITICAL FIX: Use UserRole enum, not string
        test_user = User(
            email="test@example.com",
            username="testuser",
            full_name="Test User",
            password_hash=get_password_hash("password123"),  # ✅ FIXED
            role=UserRole.USER,  # ✅ FIXED: Use enum, not string
            is_active=True,
            is_verified=True
        )
        
        session.add(test_user)
        await session.commit()
        await session.refresh(test_user)
        
        logger.info("✅ Test user created")
        logger.info(f"   Email: test@example.com")
        logger.info(f"   Password: password123")
        
        return test_user
        
    except Exception as e:
        logger.error(f"❌ Failed to create test user: {e}")
        import traceback
        traceback.print_exc()
        await session.rollback()
        raise


async def create_admin_user(session: AsyncSession) -> User:
    """Create admin user - FIXED to use UserRole enum"""
    try:
        result = await session.execute(
            select(User).where(User.email == "admin@example.com")
        )
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            logger.info("Admin user already exists")
            logger.info(f"   Email: {existing_user.email}")
            return existing_user
        
        # CRITICAL FIX: Use UserRole enum, not string
        admin_user = User(
            email="admin@example.com",
            username="admin",
            full_name="Administrator",
            password_hash=get_password_hash("admin123"),  # ✅ FIXED
            role=UserRole.ADMIN,  # ✅ FIXED: Use enum, not string
            is_active=True,
            is_verified=True
        )
        
        session.add(admin_user)
        await session.commit()
        await session.refresh(admin_user)
        
        logger.info("✅ Admin user created")
        logger.info(f"   Email: admin@example.com")
        logger.info(f"   Password: admin123")
        
        return admin_user
        
    except Exception as e:
        logger.error(f"❌ Failed to create admin user: {e}")
        import traceback
        traceback.print_exc()
        await session.rollback()
        raise


async def create_sample_workspace(session: AsyncSession, user: User) -> Workspace:
    """Create sample workspace"""
    try:
        result = await session.execute(
            select(Workspace).where(Workspace.created_by == user.id)
        )
        existing_workspace = result.scalar_one_or_none()
        
        if existing_workspace:
            logger.info("Workspace already exists")
            return existing_workspace
        
        workspace = Workspace(
            name=f"{user.username}'s Workspace",
            description="Personal workspace",
            type=WorkspaceType.PERSONAL,
            created_by=user.id,
            settings={},
            is_active=True
        )
        
        session.add(workspace)
        await session.commit()
        await session.refresh(workspace)
        
        logger.info("✅ Workspace created")
        
        return workspace
        
    except Exception as e:
        logger.error(f"❌ Failed to create workspace: {e}")
        await session.rollback()
        raise


async def init_falkordb():
    """Initialize FalkorDB"""
    try:
        logger.info("Initializing FalkorDB...")
        
        from app.graph.client import get_graph_client
        
        graph_client = get_graph_client()
        
        if not graph_client.is_connected():
            logger.warning("⚠️  FalkorDB connection failed - graph features will be disabled")
            return False
        
        logger.info("✅ FalkorDB initialized successfully")
        logger.info(f"   Host: {settings.FALKORDB_HOST}")
        logger.info(f"   Port: {settings.FALKORDB_PORT}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize FalkorDB: {e}")
        return False


async def main():
    """Main initialization function"""
    logger.info("=" * 60)
    logger.info("🚀 Database Initialization")
    logger.info("=" * 60)
    
    engine = create_async_engine(
        settings.ASYNC_DATABASE_URL,
        echo=settings.DEBUG,
        future=True
    )
    
    async_session = sessionmaker(
        engine, 
        class_=AsyncSession, 
        expire_on_commit=False
    )
    
    try:
        # Step 1: Verify connection
        logger.info("\n1️⃣  Verifying database connection...")
        if not await verify_connection(engine):
            return
        
        # Step 2: Check existing tables
        logger.info("\n2️⃣  Checking existing tables...")
        tables_before = await get_table_count(engine)
        logger.info(f"   Found {len(tables_before)} tables")
        
        # Step 3: Create tables
        logger.info("\n3️⃣  Creating missing tables...")
        if not await create_tables(engine):
            return
        
        # Step 4: Verify tables
        logger.info("\n4️⃣  Verifying tables...")
        tables_after = await get_table_count(engine)
        logger.info(f"   ✅ Database now has {len(tables_after)} tables")
        
        # Step 5: Create test user
        logger.info("\n5️⃣  Creating test user...")
        async with async_session() as session:
            test_user = await create_test_user(session)
        
        # Step 6: Create admin user
        logger.info("\n6️⃣  Creating admin user...")
        async with async_session() as session:
            admin_user = await create_admin_user(session)
        
        # Step 7: Create workspace
        logger.info("\n7️⃣  Creating sample workspace...")
        try:
            async with async_session() as session:
                workspace = await create_sample_workspace(session, test_user)
        except Exception as e:
            logger.error(f"❌ Error creating workspace: {e}")
        
        # Step 8: Initialize FalkorDB
        logger.info("\n8️⃣  Initializing FalkorDB...")
        falkordb_success = await init_falkordb()
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ Database initialization complete!")
        logger.info("=" * 60)
        logger.info("\nYou can now:")
        logger.info("1. Login with:")
        logger.info("   - test@example.com / password123")
        logger.info("   - admin@example.com / admin123")
        logger.info("2. API docs: http://localhost:8000/docs")
        if falkordb_success:
            logger.info("3. FalkorDB: ✓ Available")
        else:
            logger.info("3. FalkorDB: ✗ Disabled")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ Initialization failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())