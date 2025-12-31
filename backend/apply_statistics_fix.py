# backend/apply_statistics_fix.py
"""
Apply model_statistics table fix - FIXED to handle PL/pgSQL functions
Path: backend/apply_statistics_fix.py
"""
import asyncio
import sys
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)


def parse_sql_statements(sql_content: str) -> list[str]:
    """
    Parse SQL content into individual statements, properly handling:
    - PL/pgSQL functions with $$ delimiters
    - Multi-line statements
    - Comments
    
    Args:
        sql_content: Raw SQL content
        
    Returns:
        List of complete SQL statements
    """
    statements = []
    current_statement = []
    in_dollar_quote = False
    dollar_tag = None
    
    lines = sql_content.split('\n')
    
    for line in lines:
        stripped = line.strip()
        
        # Skip empty lines and comments outside of functions
        if not in_dollar_quote and (not stripped or stripped.startswith('--')):
            continue
        
        # Check for dollar-quoted strings ($$, $tag$, etc.)
        dollar_matches = re.finditer(r'\$(\w*)\$', line)
        for match in dollar_matches:
            tag = match.group(1)
            if not in_dollar_quote:
                # Starting a dollar-quoted block
                in_dollar_quote = True
                dollar_tag = tag
            elif tag == dollar_tag:
                # Ending the dollar-quoted block
                in_dollar_quote = False
                dollar_tag = None
        
        current_statement.append(line)
        
        # If not in a dollar-quoted block and line ends with semicolon, it's a complete statement
        if not in_dollar_quote and stripped.endswith(';'):
            statement = '\n'.join(current_statement).strip()
            if statement:
                statements.append(statement)
            current_statement = []
    
    # Add any remaining statement
    if current_statement:
        statement = '\n'.join(current_statement).strip()
        if statement:
            statements.append(statement)
    
    return statements


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
        
        logger.info("Parsing SQL statements...")
        
        # Parse SQL properly, handling PL/pgSQL functions
        statements = parse_sql_statements(sql_content)
        
        logger.info(f"Found {len(statements)} SQL statements to execute")
        
        async with engine.begin() as conn:
            for i, statement in enumerate(statements, 1):
                try:
                    # Show preview of statement (first 100 chars)
                    preview = statement[:100].replace('\n', ' ')
                    if len(statement) > 100:
                        preview += "..."
                    logger.info(f"Executing statement {i}/{len(statements)}: {preview}")
                    
                    await conn.execute(text(statement))
                    logger.info(f"✓ Statement {i} executed successfully")
                    
                except Exception as e:
                    error_msg = str(e)
                    # Some statements might fail if already exist
                    if any(keyword in error_msg.lower() for keyword in ['already exists', 'duplicate', 'does not exist']):
                        logger.warning(f"Statement {i} warning (might be ok): {error_msg}")
                    else:
                        logger.error(f"❌ Statement {i} failed: {error_msg}")
                        logger.error(f"Statement was: {statement[:200]}")
                        raise
        
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
                
                # Check table structure
                result = await conn.execute(text("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'model_statistics'
                    ORDER BY ordinal_position
                """))
                columns = result.fetchall()
                logger.info(f"   Table has {len(columns)} columns:")
                for col in columns:
                    logger.info(f"   - {col[0]}: {col[1]}")
                
                # Count rows
                result = await conn.execute(text("SELECT COUNT(*) FROM model_statistics"))
                count = result.scalar()
                logger.info(f"   Statistics rows: {count}")
                
                # Verify triggers exist
                result = await conn.execute(text("""
                    SELECT trigger_name 
                    FROM information_schema.triggers 
                    WHERE event_object_table IN ('models', 'diagrams', 'model_statistics')
                    ORDER BY trigger_name
                """))
                triggers = result.fetchall()
                logger.info(f"   Found {len(triggers)} related triggers:")
                for trigger in triggers:
                    logger.info(f"   - {trigger[0]}")
                
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