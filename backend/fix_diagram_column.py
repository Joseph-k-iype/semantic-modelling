# backend/fix_diagram_column.py
"""
Direct Database Fix Script - Rename notation_type to notation

Path: backend/fix_diagram_column.py

Run this script to fix the column name mismatch:
    cd backend
    python fix_diagram_column.py

CRITICAL FIX: This script renames 'notation_type' to 'notation' in the diagrams table
to match the SQL schema and resolve the "'type' is an invalid keyword argument" error.
"""
import asyncio
from sqlalchemy import text
from app.db.session import AsyncSessionLocal
from app.core.config import settings
import structlog

logger = structlog.get_logger()


async def check_and_fix_diagram_column():
    """Check and fix diagram column naming"""
    
    print("=" * 80)
    print("DIAGRAM COLUMN FIX SCRIPT")
    print("=" * 80)
    print()
    
    async with AsyncSessionLocal() as db:
        try:
            # Check current column names in diagrams table
            print("🔍 Checking current column structure...")
            
            check_query = text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'diagrams' 
                AND column_name IN ('notation', 'notation_type')
                ORDER BY column_name;
            """)
            
            result = await db.execute(check_query)
            columns = result.fetchall()
            
            print(f"Found columns: {[col[0] for col in columns]}")
            print()
            
            has_notation = any(col[0] == 'notation' for col in columns)
            has_notation_type = any(col[0] == 'notation_type' for col in columns)
            
            if has_notation and not has_notation_type:
                print("✅ Column 'notation' already exists and 'notation_type' doesn't exist")
                print("✅ No fix needed - database is already correct!")
                return True
            
            elif has_notation_type and not has_notation:
                print("⚠️  Found 'notation_type' but 'notation' doesn't exist")
                print("🔧 Renaming 'notation_type' to 'notation'...")
                
                # Rename the column
                rename_query = text("""
                    ALTER TABLE diagrams 
                    RENAME COLUMN notation_type TO notation;
                """)
                
                await db.execute(rename_query)
                await db.commit()
                
                print("✅ Successfully renamed 'notation_type' to 'notation'!")
                
                # Verify the change
                verify_result = await db.execute(check_query)
                verify_columns = verify_result.fetchall()
                print(f"✅ Verified - Current columns: {[col[0] for col in verify_columns]}")
                
                return True
            
            elif has_notation and has_notation_type:
                print("⚠️  WARNING: Both 'notation' and 'notation_type' columns exist!")
                print("This is an unexpected state. Please check your database schema.")
                return False
            
            else:
                print("⚠️  Neither 'notation' nor 'notation_type' found!")
                print("This might be a fresh database. Run migrations to create the table.")
                return False
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            print(f"Error type: {type(e).__name__}")
            await db.rollback()
            return False


async def verify_diagram_table():
    """Verify the diagrams table structure"""
    
    print()
    print("=" * 80)
    print("VERIFYING DIAGRAMS TABLE STRUCTURE")
    print("=" * 80)
    print()
    
    async with AsyncSessionLocal() as db:
        try:
            # Get all columns in diagrams table
            query = text("""
                SELECT 
                    column_name, 
                    data_type, 
                    is_nullable,
                    column_default
                FROM information_schema.columns 
                WHERE table_name = 'diagrams'
                ORDER BY ordinal_position;
            """)
            
            result = await db.execute(query)
            columns = result.fetchall()
            
            print("Current diagrams table structure:")
            print("-" * 80)
            print(f"{'Column Name':<30} {'Data Type':<20} {'Nullable':<10} {'Default':<20}")
            print("-" * 80)
            
            for col in columns:
                nullable = "YES" if col[2] == "YES" else "NO"
                default = str(col[3])[:20] if col[3] else ""
                print(f"{col[0]:<30} {col[1]:<20} {nullable:<10} {default:<20}")
            
            print("-" * 80)
            print(f"Total columns: {len(columns)}")
            print()
            
            # Check if 'notation' column exists
            has_notation = any(col[0] == 'notation' for col in columns)
            
            if has_notation:
                print("✅ 'notation' column found - correct!")
            else:
                print("❌ 'notation' column NOT found - database needs fixing!")
            
            return has_notation
            
        except Exception as e:
            print(f"❌ Error verifying table: {str(e)}")
            return False


async def main():
    """Main execution function"""
    
    print()
    print("🚀 Starting database fix process...")
    print()
    
    # Step 1: Check and fix column
    fix_success = await check_and_fix_diagram_column()
    
    if not fix_success:
        print()
        print("❌ Fix failed or not applicable")
        return
    
    # Step 2: Verify final state
    verify_success = await verify_diagram_table()
    
    print()
    print("=" * 80)
    if verify_success:
        print("✅ SUCCESS: Database is now correctly configured!")
        print("✅ The 'notation' column is ready for use.")
        print()
        print("Next steps:")
        print("1. Restart the backend service: docker-compose restart backend")
        print("2. Test diagram creation from the frontend")
    else:
        print("⚠️  WARNING: Verification failed")
        print("Please check the database schema manually")
    print("=" * 80)
    print()


if __name__ == "__main__":
    asyncio.run(main())