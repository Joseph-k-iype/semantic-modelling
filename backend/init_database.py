# backend/init_database.py
"""
Database Initialization Script - COMPLETE FIX
Path: backend/init_database.py

CRITICAL FIXES:
- Uses password_hash (not hashed_password)
- Uses UserRole enum properly
- Does NOT set created_by/updated_by (let trigger handle them)
- Properly creates test users and data
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime
import uuid

import structlog

# Add the app directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import engine, AsyncSessionLocal
from app.db.base import Base
from app.models.user import User, UserRole
from app.core.security import get_password_hash

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.dev.ConsoleRenderer()
    ]
)

logger = structlog.get_logger()


async def verify_connection():
    """Verify database connection"""
    logger.info("1️⃣  Verifying database connection...")
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT 1"))
            result.scalar()
            logger.info("✅ Database connection successful")
            return True
    except Exception as e:
        logger.error("❌ Database connection failed", error=str(e))
        return False


async def check_existing_tables():
    """Check existing tables in the database"""
    logger.info("2️⃣  Checking existing tables...")
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            )
            tables = [row[0] for row in result.fetchall()]
            logger.info(f"   Found {len(tables)} tables")
            return tables
    except Exception as e:
        logger.error("❌ Failed to check tables", error=str(e))
        return []


async def create_tables():
    """Create all tables defined in models"""
    logger.info("3️⃣  Creating missing tables...")
    try:
        async with engine.begin() as conn:
            # Import all models to ensure they're registered
            from app.models import user  # noqa
            
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("✅ All tables created successfully")
        return True
    except Exception as e:
        logger.error("❌ Failed to create tables", error=str(e))
        import traceback
        traceback.print_exc()
        return False


async def create_test_user(session: AsyncSession):
    """
    Create a test user for development
    
    CRITICAL: Does NOT set created_by/updated_by - the database trigger handles this
    """
    logger.info("5️⃣  Creating test user...")
    
    try:
        # Check if user already exists
        result = await session.execute(
            select(User).where(User.email == "test@example.com")
        )
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            logger.info(f"   ℹ️  Test user already exists: {existing_user.email}")
            return existing_user
        
        # Create test user
        # CRITICAL: Do NOT set created_by or updated_by - trigger handles them
        test_user = User(
            email="test@example.com",
            username="testuser",
            full_name="Test User",
            password_hash=get_password_hash("password123"),  # ✅ FIXED: Use password_hash
            role=UserRole.USER,  # ✅ FIXED: Use enum
            is_active=True,
            is_verified=True
            # ✅ CRITICAL: Do NOT set created_by or updated_by
        )
        
        session.add(test_user)
        await session.commit()
        await session.refresh(test_user)
        
        logger.info(f"   ✅ Test user created: {test_user.email} / password123")
        return test_user
        
    except Exception as e:
        logger.error("❌ Failed to create test user", error=str(e))
        import traceback
        traceback.print_exc()
        await session.rollback()
        raise


async def create_admin_user(session: AsyncSession):
    """
    Create an admin user for development
    
    CRITICAL: Does NOT set created_by/updated_by - the database trigger handles this
    """
    logger.info("6️⃣  Creating admin user...")
    
    try:
        # Check if admin already exists
        result = await session.execute(
            select(User).where(User.email == "admin@example.com")
        )
        existing_admin = result.scalar_one_or_none()
        
        if existing_admin:
            logger.info(f"   ℹ️  Admin user already exists: {existing_admin.email}")
            return existing_admin
        
        # Create admin user
        # CRITICAL: Do NOT set created_by or updated_by - trigger handles them
        admin_user = User(
            email="admin@example.com",
            username="admin",
            full_name="Admin User",
            password_hash=get_password_hash("Admin@123"),  # ✅ FIXED: Use password_hash
            role=UserRole.ADMIN,  # ✅ FIXED: Use enum
            is_active=True,
            is_verified=True
            # ✅ CRITICAL: Do NOT set created_by or updated_by
        )
        
        session.add(admin_user)
        await session.commit()
        await session.refresh(admin_user)
        
        logger.info(f"   ✅ Admin user created: {admin_user.email} / Admin@123")
        return admin_user
        
    except Exception as e:
        logger.error("❌ Failed to create admin user", error=str(e))
        import traceback
        traceback.print_exc()
        await session.rollback()
        raise


async def verify_tables():
    """Verify all tables were created"""
    logger.info("4️⃣  Verifying tables...")
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            )
            tables = [row[0] for row in result.fetchall()]
            logger.info(f"   ✅ Database now has {len(tables)} tables")
            return tables
    except Exception as e:
        logger.error("❌ Failed to verify tables", error=str(e))
        return []


async def print_summary(test_user, admin_user):
    """Print initialization summary"""
    logger.info("="*60)
    logger.info("✅ Database Initialization Complete!")
    logger.info("="*60)
    logger.info("")
    logger.info("Test Credentials:")
    logger.info(f"  Email:    {test_user.email}")
    logger.info(f"  Password: password123")
    logger.info(f"  Role:     {test_user.role.value}")
    logger.info("")
    logger.info("Admin Credentials:")
    logger.info(f"  Email:    {admin_user.email}")
    logger.info(f"  Password: Admin@123")
    logger.info(f"  Role:     {admin_user.role.value}")
    logger.info("")
    logger.info("API Endpoints:")
    logger.info("  Backend:  http://localhost:8000")
    logger.info("  Docs:     http://localhost:8000/docs")
    logger.info("  Frontend: http://localhost:5173")
    logger.info("")
    logger.info("Test Login:")
    logger.info('  curl -X POST http://localhost:8000/api/v1/auth/login \\')
    logger.info('    -H "Content-Type: application/json" \\')
    logger.info(f'    -d \'{{"email":"{test_user.email}","password":"password123"}}\'')
    logger.info("="*60)


async def main():
    """Main initialization function"""
    logger.info("="*60)
    logger.info("🚀 Database Initialization")
    logger.info("="*60)
    logger.info("")
    
    try:
        # Step 1: Verify connection
        if not await verify_connection():
            logger.error("❌ Initialization failed: Cannot connect to database")
            sys.exit(1)
        
        logger.info("")
        
        # Step 2: Check existing tables
        await check_existing_tables()
        logger.info("")
        
        # Step 3: Create tables
        if not await create_tables():
            logger.error("❌ Initialization failed: Cannot create tables")
            sys.exit(1)
        
        logger.info("")
        
        # Step 4: Verify tables
        await verify_tables()
        logger.info("")
        
        # Step 5 & 6: Create users
        async with AsyncSessionLocal() as session:
            test_user = await create_test_user(session)
            logger.info("")
            admin_user = await create_admin_user(session)
        
        logger.info("")
        
        # Print summary
        await print_summary(test_user, admin_user)
        
    except Exception as e:
        logger.error("❌ Initialization failed", error=str(e))
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())