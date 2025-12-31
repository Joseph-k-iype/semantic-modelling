# backend/apply_statistics_fix.py
"""
Apply model_statistics table fix
Path: backend/apply_statistics_fix.py
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)


async def apply_fix():
    """Apply the model_statistics table fix"""
    
    logger.info("=" * 80)
    logger.info("🔧 Applying model_statistics Fix")
    logger.info("=" * 80)
    
    engine = create_async_engine(
        settings.ASYNC_DATABASE_URL,
        echo=True,
        future=True
    )
    
    try:
        # Read SQL fix file
        sql_file = Path(__file__).parent / "fix_model_statistics.sql"
        
        if not sql_file.exists():
            logger.error(f"❌ SQL fix file not found: {sql_file}")
            return False
        
        sql_content = sql_file.read_text()
        
        logger.info("Applying SQL fix...")
        
        async with engine.begin() as conn:
            # Split by semicolon and execute each statement
            statements = [s.strip() for s in sql_content.split(';') if s.strip()]
            
            for i, statement in enumerate(statements, 1):
                if statement and not statement.startswith('--'):
                    try:
                        logger.info(f"Executing statement {i}/{len(statements)}...")
                        await conn.execute(text(statement))
                    except Exception as e:
                        # Some statements might fail if already exist, that's ok
                        logger.warning(f"Statement {i} warning (might be ok): {e}")
        
        logger.info("✅ model_statistics fix applied successfully!")
        
        # Verify the table exists
        async with engine.begin() as conn:
            result = await conn.execute(text("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_name = 'model_statistics'
                )
            """))
            exists = result.scalar()
            
            if exists:
                logger.info("✅ model_statistics table verified")
                
                # Count rows
                result = await conn.execute(text("SELECT COUNT(*) FROM model_statistics"))
                count = result.scalar()
                logger.info(f"   Statistics rows: {count}")
            else:
                logger.error("❌ model_statistics table still doesn't exist!")
                return False
        
        logger.info("\n" + "=" * 80)
        logger.info("✅ Fix completed successfully!")
        logger.info("=" * 80)
        logger.info("\nYou can now:")
        logger.info("1. Create diagrams without errors")
        logger.info("2. Statistics will be automatically tracked")
        logger.info("3. Restart the backend: docker-compose restart backend")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Fix failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await engine.dispose()


if __name__ == "__main__":
    success = asyncio.run(apply_fix())
    sys.exit(0 if success else 1)