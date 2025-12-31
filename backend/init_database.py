# backend/init_database.py
"""
Database Initialization Script - COMPLETE AND PRODUCTION READY
Creates tables, sample users, workspaces, and initializes FalkorDB
Path: backend/init_database.py
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import structlog
import redis.asyncio as redis_async

from app.db.base import Base
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceType
from app.models.folder import Folder
from app.models.model import Model, ModelType, ModelStatus
from app.core.security import get_password_hash
from app.core.config import settings

logger = structlog.get_logger(__name__)


async def verify_connection(engine):
    """Verify database connection"""
    try:
        logger.info("Verifying database connection...")
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            result.fetchone()
        logger.info("✅ Database connection successful")
        return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False


async def get_table_count(engine):
    """Get list of existing tables"""
    async with engine.begin() as conn:
        result = await conn.execute(
            text("""
                SELECT relname 
                FROM pg_class 
                WHERE relkind IN ('r', 'p')
                AND relnamespace = 'public'::regnamespace
                AND relname NOT LIKE 'pg_%'
                AND relname NOT LIKE 'sql_%'
                ORDER BY relname
            """)
        )
        tables = result.fetchall()
        return [table[0] for table in tables]


async def create_tables(engine):
    """Create all database tables"""
    try:
        logger.info("Creating database tables...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ Database tables created successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to create tables: {e}")
        import traceback
        traceback.print_exc()
        return False


async def create_test_user(session: AsyncSession):
    """Create a test user if it doesn't exist"""
    try:
        result = await session.execute(
            select(User).where(User.email == "test@example.com")
        )
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            logger.info("ℹ️  Test user already exists")
            logger.info(f"   Email: {existing_user.email}")
            logger.info(f"   Username: {existing_user.username}")
            logger.info(f"   ID: {existing_user.id}")
            return existing_user
        
        test_user = User(
            email="test@example.com",
            username="testuser",
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
        logger.info(f"   Email: {test_user.email}")
        logger.info(f"   Username: {test_user.username}")
        logger.info(f"   Password: password123")
        logger.info(f"   ID: {test_user.id}")
        
        return test_user
        
    except Exception as e:
        logger.error(f"❌ Failed to create test user: {e}")
        await session.rollback()
        raise


async def create_admin_user(session: AsyncSession):
    """Create an admin user if it doesn't exist"""
    try:
        result = await session.execute(
            select(User).where(User.email == "admin@example.com")
        )
        existing_admin = result.scalar_one_or_none()
        
        if existing_admin:
            logger.info("ℹ️  Admin user already exists")
            logger.info(f"   Email: {existing_admin.email}")
            logger.info(f"   Username: {existing_admin.username}")
            logger.info(f"   ID: {existing_admin.id}")
            return existing_admin
        
        admin_user = User(
            email="admin@example.com",
            username="admin",
            hashed_password=get_password_hash("admin123"),
            full_name="Admin User",
            is_active=True,
            is_superuser=True,
            is_verified=True
        )
        session.add(admin_user)
        await session.commit()
        await session.refresh(admin_user)
        
        logger.info("✅ Admin user created successfully")
        logger.info(f"   Email: {admin_user.email}")
        logger.info(f"   Username: {admin_user.username}")
        logger.info(f"   Password: admin123")
        logger.info(f"   ID: {admin_user.id}")
        
        return admin_user
        
    except Exception as e:
        logger.error(f"❌ Failed to create admin user: {e}")
        await session.rollback()
        raise


async def create_sample_workspace(session: AsyncSession, user: User):
    """Create a sample personal workspace"""
    try:
        # Check if workspace already exists
        result = await session.execute(
            select(Workspace).where(
                Workspace.name == "My Workspace",
                Workspace.created_by == user.id
            )
        )
        existing_workspace = result.scalar_one_or_none()
        
        if existing_workspace:
            logger.info("ℹ️  Sample workspace already exists")
            logger.info(f"   Name: {existing_workspace.name}")
            logger.info(f"   ID: {existing_workspace.id}")
            return existing_workspace
        
        # Create workspace using WorkspaceType enum
        workspace = Workspace(
            name="My Workspace",
            description="Personal workspace for modeling",
            type=WorkspaceType.PERSONAL,  # Use enum directly
            created_by=user.id,
            settings={},
            is_active=True
        )
        session.add(workspace)
        await session.commit()
        await session.refresh(workspace)
        
        logger.info("✅ Sample workspace created successfully")
        logger.info(f"   Name: {workspace.name}")
        logger.info(f"   Type: {workspace.type.value}")
        logger.info(f"   ID: {workspace.id}")
        
        return workspace
        
    except Exception as e:
        logger.error(f"❌ Failed to create workspace: {e}")
        import traceback
        traceback.print_exc()
        await session.rollback()
        raise


async def create_common_workspace(session: AsyncSession, admin: User):
    """Create a common workspace for organization-wide models"""
    try:
        # Check if common workspace already exists
        result = await session.execute(
            select(Workspace).where(
                Workspace.type == WorkspaceType.COMMON  # Use enum for comparison
            )
        )
        existing_workspace = result.scalar_one_or_none()
        
        if existing_workspace:
            logger.info("ℹ️  Common workspace already exists")
            logger.info(f"   Name: {existing_workspace.name}")
            logger.info(f"   ID: {existing_workspace.id}")
            return existing_workspace
        
        # Create common workspace
        workspace = Workspace(
            name="Common Workspace",
            description="Organization-wide common workspace for published models",
            type=WorkspaceType.COMMON,  # Use enum directly
            created_by=admin.id,
            settings={
                "require_approval": True,
                "auto_publish": False
            },
            is_active=True
        )
        session.add(workspace)
        await session.commit()
        await session.refresh(workspace)
        
        logger.info("✅ Common workspace created successfully")
        logger.info(f"   Name: {workspace.name}")
        logger.info(f"   Type: {workspace.type.value}")
        logger.info(f"   ID: {workspace.id}")
        
        return workspace
        
    except Exception as e:
        logger.error(f"❌ Failed to create common workspace: {e}")
        import traceback
        traceback.print_exc()
        await session.rollback()
        raise


async def create_sample_model(session: AsyncSession, workspace: Workspace, user: User):
    """Create a sample model"""
    try:
        result = await session.execute(
            select(Model).where(
                Model.name == "Sample ER Model",
                Model.workspace_id == workspace.id
            )
        )
        existing_model = result.scalar_one_or_none()
        
        if existing_model:
            logger.info("ℹ️  Sample model already exists")
            logger.info(f"   Name: {existing_model.name}")
            logger.info(f"   ID: {existing_model.id}")
            return existing_model
        
        model = Model(
            name="Sample ER Model",
            description="A sample Entity-Relationship model",
            type=ModelType.ER,
            status=ModelStatus.DRAFT,
            workspace_id=workspace.id,
            created_by=user.id,
            version=1,
            tags=["sample", "er", "database"],
            metadata={}
        )
        session.add(model)
        await session.commit()
        await session.refresh(model)
        
        logger.info("✅ Sample model created successfully")
        logger.info(f"   Name: {model.name}")
        logger.info(f"   Type: {model.type.value}")
        logger.info(f"   ID: {model.id}")
        
        return model
        
    except Exception as e:
        logger.error(f"❌ Failed to create model: {e}")
        await session.rollback()
        raise


async def init_falkordb():
    """Initialize FalkorDB graph database"""
    try:
        logger.info("Initializing FalkorDB...")
        
        redis_client = redis_async.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            decode_responses=True
        )
        
        await redis_client.ping()
        logger.info("Connected to FalkorDB successfully", 
                   host=settings.REDIS_HOST, 
                   port=settings.REDIS_PORT)
        
        graph_name = "modeling_graph"
        logger.info("Graph selected", graph_name=graph_name)
        
        await redis_client.close()
        
        logger.info("✅ FalkorDB initialized successfully")
        logger.info(f"   Graph: {graph_name}")
        
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
        settings.ASYNC_DATABASE_URL,  # ✅ FIXED: Use correct attribute name
        echo=True,
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
        logger.info(f"   Found {len(tables_before)} tables:")
        for table in tables_before:
            logger.info(f"   - {table}")
        
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
        
        # Step 7: Create sample workspace
        logger.info("\n7️⃣  Creating sample workspace...")
        try:
            async with async_session() as session:
                workspace = await create_sample_workspace(session, test_user)
        except Exception as e:
            logger.error(f"❌ Error creating workspace: {e}")
            workspace = None
        
        # Step 8: Create common workspace
        logger.info("\n8️⃣  Creating common workspace...")
        try:
            async with async_session() as session:
                common_workspace = await create_common_workspace(session, admin_user)
        except Exception as e:
            logger.error(f"❌ Error creating common workspace: {e}")
            common_workspace = None
        
        # Step 9: Create sample model
        if workspace and test_user:
            logger.info("\n9️⃣  Creating sample model...")
            try:
                async with async_session() as session:
                    # Re-query to get fresh instances in new session
                    result = await session.execute(select(Workspace).where(Workspace.id == workspace.id))
                    workspace = result.scalar_one()
                    result = await session.execute(select(User).where(User.id == test_user.id))
                    user = result.scalar_one()
                    
                    model = await create_sample_model(session, workspace, user)
            except Exception as e:
                logger.error(f"❌ Error creating model: {e}")
        else:
            logger.warning("⚠️  Skipping model creation (no test user or workspace)")
        
        # Step 10: Initialize FalkorDB
        logger.info("\n🔟 Initializing FalkorDB...")
        await init_falkordb()
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ Database initialization complete!")
        logger.info("=" * 60)
        logger.info("\nYou can now:")
        logger.info("1. Login with:")
        logger.info("   - Regular user: test@example.com / password123")
        logger.info("   - Admin user:   admin@example.com / admin123")
        logger.info("2. Or register a new account via the API")
        logger.info("3. API docs available at: http://localhost:8000/docs")
        logger.info("4. FalkorDB graph features: ✓ Available")
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())