"""
Database initialization script - COMPLETE AND FIXED
Creates all tables if they don't exist and handles proper model imports
Path: backend/init_database.py
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import inspect, text
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

# Configure logging - FIXED: Use min_level instead of logging_level
structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(min_level=20),
)

logger = structlog.get_logger()


async def check_tables_exist():
    """Check if database tables exist"""
    async with engine.begin() as conn:
        result = await conn.run_sync(
            lambda sync_conn: inspect(sync_conn).get_table_names()
        )
        return result


async def verify_connection():
    """Verify database connection"""
    logger.info("Verifying database connection...")
    try:
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            logger.info("✅ Database connection successful")
            return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {str(e)}")
        return False


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
                logger.info(f"   Email: {existing_user.email}")
                logger.info(f"   Username: {existing_user.username}")
                logger.info(f"   ID: {existing_user.id}")
                return existing_user
            
            # Create test user
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


async def create_admin_user():
    """Create an admin user for development"""
    from sqlalchemy import select
    
    async with AsyncSessionLocal() as session:
        try:
            # Check if admin user already exists
            result = await session.execute(
                select(User).where(User.email == "admin@example.com")
            )
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                logger.info("ℹ️  Admin user already exists")
                logger.info(f"   Email: {existing_user.email}")
                logger.info(f"   Username: {existing_user.username}")
                logger.info(f"   ID: {existing_user.id}")
                return existing_user
            
            # Create admin user
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
            logger.info(f"   Email: admin@example.com")
            logger.info(f"   Username: admin")
            logger.info(f"   Password: admin123")
            logger.info(f"   ID: {admin_user.id}")
            
            return admin_user
            
        except Exception as e:
            logger.error(f"❌ Failed to create admin user: {str(e)}")
            import traceback
            traceback.print_exc()
            await session.rollback()
            raise


async def create_sample_workspace(user: User):
    """Create a sample workspace for testing"""
    from sqlalchemy import select
    
    async with AsyncSessionLocal() as session:
        try:
            # Check if workspace already exists
            result = await session.execute(
                select(Workspace).where(
                    Workspace.name == "My Workspace",
                    Workspace.owner_id == user.id
                )
            )
            existing_workspace = result.scalar_one_or_none()
            
            if existing_workspace:
                logger.info("ℹ️  Sample workspace already exists")
                logger.info(f"   Name: {existing_workspace.name}")
                logger.info(f"   ID: {existing_workspace.id}")
                return existing_workspace
            
            # Create workspace
            workspace = Workspace(
                name="My Workspace",
                description="Personal workspace for modeling projects",
                workspace_type="personal",
                owner_id=user.id
            )
            
            session.add(workspace)
            await session.commit()
            await session.refresh(workspace)
            
            logger.info("✅ Sample workspace created successfully")
            logger.info(f"   Name: {workspace.name}")
            logger.info(f"   Type: {workspace.workspace_type}")
            logger.info(f"   ID: {workspace.id}")
            
            return workspace
            
        except Exception as e:
            logger.error(f"❌ Failed to create workspace: {str(e)}")
            import traceback
            traceback.print_exc()
            await session.rollback()
            raise


async def create_common_workspace(user: User):
    """Create a common workspace for organization-wide models"""
    from sqlalchemy import select
    
    async with AsyncSessionLocal() as session:
        try:
            # Check if common workspace already exists
            result = await session.execute(
                select(Workspace).where(
                    Workspace.name == "Common Workspace",
                    Workspace.workspace_type == "common"
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
                description="Organization-wide canonical models",
                workspace_type="common",
                owner_id=user.id
            )
            
            session.add(workspace)
            await session.commit()
            await session.refresh(workspace)
            
            logger.info("✅ Common workspace created successfully")
            logger.info(f"   Name: {workspace.name}")
            logger.info(f"   Type: {workspace.workspace_type}")
            logger.info(f"   ID: {workspace.id}")
            
            return workspace
            
        except Exception as e:
            logger.error(f"❌ Failed to create common workspace: {str(e)}")
            import traceback
            traceback.print_exc()
            await session.rollback()
            raise


async def create_sample_model(user: User, workspace: Workspace):
    """Create a sample ER model for testing"""
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
                logger.info(f"   Name: {existing_model.name}")
                logger.info(f"   ID: {existing_model.id}")
                return existing_model
            
            # Create model with sample ER data
            model_data = {
                "entities": [
                    {
                        "id": "entity-1",
                        "name": "Customer",
                        "attributes": [
                            {"name": "customer_id", "type": "INTEGER", "isPrimaryKey": True},
                            {"name": "name", "type": "VARCHAR(100)"},
                            {"name": "email", "type": "VARCHAR(255)"}
                        ]
                    },
                    {
                        "id": "entity-2",
                        "name": "Order",
                        "attributes": [
                            {"name": "order_id", "type": "INTEGER", "isPrimaryKey": True},
                            {"name": "customer_id", "type": "INTEGER", "isForeignKey": True},
                            {"name": "order_date", "type": "TIMESTAMP"},
                            {"name": "total", "type": "DECIMAL(10,2)"}
                        ]
                    }
                ],
                "relationships": [
                    {
                        "id": "rel-1",
                        "source": "entity-1",
                        "target": "entity-2",
                        "type": "one-to-many",
                        "label": "places"
                    }
                ]
            }
            
            model = Model(
                name="Sample ER Model",
                description="A sample entity-relationship model for testing",
                model_type="er",
                workspace_id=workspace.id,
                created_by=user.id,
                data=model_data
            )
            
            session.add(model)
            await session.commit()
            await session.refresh(model)
            
            logger.info("✅ Sample model created successfully")
            logger.info(f"   Name: {model.name}")
            logger.info(f"   Type: {model.model_type}")
            logger.info(f"   ID: {model.id}")
            
            return model
            
        except Exception as e:
            logger.error(f"❌ Failed to create model: {str(e)}")
            import traceback
            traceback.print_exc()
            await session.rollback()
            raise


async def initialize_falkordb():
    """Initialize FalkorDB graph database"""
    logger.info("Initializing FalkorDB...")
    
    try:
        from app.graph.client import get_graph_client
        
        graph_client = get_graph_client()
        
        if not graph_client.is_connected():
            logger.warning("⚠️  FalkorDB not connected - graph features will be disabled")
            return False
        
        # Create a test graph to verify connection
        test_graph = graph_client.get_graph("modeling_graph")
        if test_graph:
            logger.info("✅ FalkorDB initialized successfully")
            logger.info(f"   Graph: modeling_graph")
            return True
        else:
            logger.warning("⚠️  Could not create test graph in FalkorDB")
            return False
            
    except Exception as e:
        logger.warning(f"⚠️  FalkorDB initialization failed: {str(e)}")
        logger.warning("   Graph features will be disabled")
        return False


async def main():
    """Main initialization function"""
    logger.info("=" * 60)
    logger.info("🚀 Database Initialization")
    logger.info("=" * 60)
    
    # Step 1: Verify connection
    logger.info("\n1️⃣  Verifying database connection...")
    if not await verify_connection():
        logger.error("❌ Cannot proceed without database connection")
        return
    
    # Step 2: Check existing tables
    logger.info("\n2️⃣  Checking existing tables...")
    existing_tables = await check_tables_exist()
    if existing_tables:
        logger.info(f"   Found {len(existing_tables)} tables:")
        for table in sorted(existing_tables):
            logger.info(f"   - {table}")
    else:
        logger.info("   No tables found")
    
    # Step 3: Create tables (if they don't exist)
    logger.info("\n3️⃣  Creating missing tables...")
    success = await create_tables()
    if not success:
        logger.error("❌ Failed to create tables. Exiting.")
        return
    
    # Step 4: Verify tables
    logger.info("\n4️⃣  Verifying tables...")
    new_tables = await check_tables_exist()
    logger.info(f"   ✅ Database now has {len(new_tables)} tables")
    
    # Step 5: Create test user
    logger.info("\n5️⃣  Creating test user...")
    try:
        test_user = await create_test_user()
    except Exception as e:
        logger.error(f"❌ Error creating test user: {str(e)}")
        test_user = None
    
    # Step 6: Create admin user
    logger.info("\n6️⃣  Creating admin user...")
    try:
        admin_user = await create_admin_user()
    except Exception as e:
        logger.error(f"❌ Error creating admin user: {str(e)}")
        admin_user = None
    
    # Step 7: Create sample workspace
    if test_user:
        logger.info("\n7️⃣  Creating sample workspace...")
        try:
            workspace = await create_sample_workspace(test_user)
        except Exception as e:
            logger.error(f"❌ Error creating workspace: {str(e)}")
            workspace = None
    else:
        workspace = None
        logger.warning("⚠️  Skipping workspace creation (no test user)")
    
    # Step 8: Create common workspace
    if admin_user:
        logger.info("\n8️⃣  Creating common workspace...")
        try:
            common_workspace = await create_common_workspace(admin_user)
        except Exception as e:
            logger.error(f"❌ Error creating common workspace: {str(e)}")
            common_workspace = None
    else:
        common_workspace = None
        logger.warning("⚠️  Skipping common workspace creation (no admin user)")
    
    # Step 9: Create sample model
    if test_user and workspace:
        logger.info("\n9️⃣  Creating sample model...")
        try:
            model = await create_sample_model(test_user, workspace)
        except Exception as e:
            logger.error(f"❌ Error creating model: {str(e)}")
    else:
        logger.warning("⚠️  Skipping model creation (no test user or workspace)")
    
    # Step 10: Initialize FalkorDB
    logger.info("\n🔟 Initializing FalkorDB...")
    falkordb_initialized = await initialize_falkordb()
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("✅ Database initialization complete!")
    logger.info("=" * 60)
    logger.info("\nYou can now:")
    logger.info("1. Login with:")
    logger.info("   - Regular user: test@example.com / password123")
    logger.info("   - Admin user:   admin@example.com / admin123")
    logger.info("2. Or register a new account via the API")
    logger.info("3. API docs available at: http://localhost:8000/docs")
    logger.info(f"4. FalkorDB graph features: {'✓ Available' if falkordb_initialized else '✗ Not available'}")
    logger.info("")


if __name__ == "__main__":
    asyncio.run(main())