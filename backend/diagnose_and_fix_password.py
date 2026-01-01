#!/usr/bin/env python3
# backend/diagnose_and_fix_password.py
"""
Diagnose and fix admin password issue
Run: docker-compose -f docker-compose.dev.yml exec backend python diagnose_and_fix_password.py
"""

import asyncio
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select, text
from app.db.session import AsyncSessionLocal
from app.models.user import User
import bcrypt


async def main():
    print("\n" + "="*80)
    print("🔍 PASSWORD DIAGNOSTIC AND FIX TOOL")
    print("="*80 + "\n")
    
    async with AsyncSessionLocal() as session:
        # Step 1: Check if admin user exists
        print("Step 1: Looking for admin user...")
        result = await session.execute(
            select(User).where(User.email == "admin@enterprise-modeling.com")
        )
        admin = result.scalar_one_or_none()
        
        if not admin:
            print("❌ Admin user not found!")
            print("   The database might not have been initialized with 01-users.sql")
            print("\n   Run this to check:")
            print("   docker exec modeling-postgres psql -U modeling -d modeling_platform -c \"SELECT email FROM users;\"")
            return
        
        print(f"✅ Found admin user:")
        print(f"   Email: {admin.email}")
        print(f"   Username: {admin.username}")
        print(f"   Role: {admin.role}")
        print(f"   Password hash starts with: {admin.password_hash[:20]}...")
        
        # Step 2: Check current password hash
        print(f"\n" + "-"*80)
        print("Step 2: Checking current password hash...")
        print(f"   Hash algorithm: {'bcrypt' if admin.password_hash.startswith('$2b$') else 'unknown'}")
        print(f"   Hash rounds: {admin.password_hash.split('$')[2] if admin.password_hash.startswith('$2b$') else 'unknown'}")
        
        # Step 3: Test password verification
        print(f"\n" + "-"*80)
        print("Step 3: Testing password verification...")
        
        test_passwords = [
            "Admin@123",
            "admin123", 
            "password123",
            "Admin123"
        ]
        
        for test_pwd in test_passwords:
            try:
                is_valid = bcrypt.checkpw(
                    test_pwd.encode('utf-8'),
                    admin.password_hash.encode('utf-8')
                )
                status = "✅ MATCH!" if is_valid else "❌ No match"
                print(f"   '{test_pwd}': {status}")
                if is_valid:
                    print(f"\n   🎉 Found working password: '{test_pwd}'")
                    print(f"   You can login with: {admin.email} / {test_pwd}")
                    return
            except Exception as e:
                print(f"   '{test_pwd}': ❌ Error - {e}")
        
        # Step 4: Generate new password
        print(f"\n" + "-"*80)
        print("Step 4: No matching password found. Generating new hash...")
        
        new_password = "Admin@123"
        print(f"   New password will be: '{new_password}'")
        
        # Generate new bcrypt hash
        salt = bcrypt.gensalt(rounds=12)
        new_hash = bcrypt.hashpw(new_password.encode('utf-8'), salt)
        new_hash_str = new_hash.decode('utf-8')
        
        print(f"   New hash generated: {new_hash_str[:20]}...")
        
        # Verify the new hash works
        print(f"\n   Verifying new hash...")
        is_valid = bcrypt.checkpw(new_password.encode('utf-8'), new_hash)
        if not is_valid:
            print("   ❌ ERROR: New hash verification failed!")
            return
        print("   ✅ New hash verified successfully!")
        
        # Step 5: Update database
        print(f"\n" + "-"*80)
        print("Step 5: Updating database...")
        
        # Use raw SQL to ensure column name is correct
        await session.execute(
            text("UPDATE users SET password_hash = :hash WHERE email = :email"),
            {"hash": new_hash_str, "email": "admin@enterprise-modeling.com"}
        )
        await session.commit()
        
        print("   ✅ Database updated!")
        
        # Step 6: Verify the update
        print(f"\n" + "-"*80)
        print("Step 6: Verifying the update...")
        
        # Refresh the user object
        await session.refresh(admin)
        
        # Test password again
        is_valid = bcrypt.checkpw(
            new_password.encode('utf-8'),
            admin.password_hash.encode('utf-8')
        )
        
        if is_valid:
            print("   ✅ Password verification successful!")
        else:
            print("   ❌ Password verification still failing!")
            return
        
        # Final summary
        print(f"\n" + "="*80)
        print("🎉 SUCCESS - PASSWORD FIXED!")
        print("="*80)
        print(f"\nLogin credentials:")
        print(f"  Email:    {admin.email}")
        print(f"  Password: {new_password}")
        print(f"\nTest with:")
        print(f'  curl -X POST http://localhost:8000/api/v1/auth/login \\')
        print(f'    -H "Content-Type: application/json" \\')
        print(f'    -d \'{{"email":"{admin.email}","password":"{new_password}"}}\'')
        print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())