# backend/reset_admin_password.py
"""
Reset admin password script - Run this to fix login issues
Path: backend/reset_admin_password.py

Usage:
    docker-compose exec backend python reset_admin_password.py
"""
import asyncio
import sys
from pathlib import Path

# Add the app directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models.user import User
from app.core.security import get_password_hash


async def reset_admin_password():
    """Reset admin user password to 'admin123'"""
    print("\n" + "="*70)
    print("🔐 ADMIN PASSWORD RESET SCRIPT")
    print("="*70 + "\n")
    
    async with AsyncSessionLocal() as session:
        try:
            # Find admin user
            result = await session.execute(
                select(User).where(User.email == "admin@example.com")
            )
            admin = result.scalar_one_or_none()
            
            if not admin:
                print("❌ Admin user not found!")
                print("   Email: admin@example.com")
                print("\n   Creating admin user...")
                
                # Create admin user
                admin = User(
                    email="admin@example.com",
                    username="admin",
                    hashed_password=get_password_hash("admin123"),
                    full_name="Admin User",
                    is_active=True,
                    is_superuser=True,
                    is_verified=True
                )
                session.add(admin)
                await session.commit()
                await session.refresh(admin)
                
                print("✅ Admin user created successfully!")
            else:
                print(f"✅ Found admin user:")
                print(f"   ID: {admin.id}")
                print(f"   Email: {admin.email}")
                print(f"   Username: {admin.username}")
                print(f"\n🔄 Resetting password...")
                
                # Reset password using NEW hashing method
                admin.hashed_password = get_password_hash("admin123")
                await session.commit()
                
                print("✅ Password reset successfully!")
            
            print("\n" + "="*70)
            print("CREDENTIALS:")
            print("="*70)
            print(f"  Email:    admin@example.com")
            print(f"  Password: admin123")
            print("="*70 + "\n")
            
            # Verify the password works
            print("🔍 Verifying password...")
            from app.core.security import verify_password
            
            if verify_password("admin123", admin.hashed_password):
                print("✅ Password verification successful!")
                print("\n✨ You can now login with the credentials above\n")
            else:
                print("❌ Password verification failed!")
                print("   There may be an issue with the security module\n")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            await session.rollback()
            raise


async def reset_test_user_password():
    """Reset test user password as well"""
    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(
                select(User).where(User.email == "test@example.com")
            )
            test_user = result.scalar_one_or_none()
            
            if test_user:
                print(f"\n🔄 Also resetting test user password...")
                test_user.hashed_password = get_password_hash("password123")
                await session.commit()
                print("✅ Test user password reset!")
                print(f"   Email:    test@example.com")
                print(f"   Password: password123\n")
            
        except Exception as e:
            print(f"⚠️  Could not reset test user: {e}")
            await session.rollback()


async def main():
    """Main function"""
    try:
        await reset_admin_password()
        await reset_test_user_password()
    except Exception as e:
        print(f"\n❌ Script failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())