# backend/cleanup-duplicate-diagrams.py
"""
Cleanup duplicate diagrams script - FIXED
Path: backend/cleanup-duplicate-diagrams.py
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select, delete, func, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import structlog

from app.core.config import settings
from app.models.diagram import Diagram

logger = structlog.get_logger(__name__)


async def cleanup_duplicates():
    """Remove duplicate diagrams, keeping only the oldest one for each name+model combination"""
    
    logger.info("=" * 80)
    logger.info("🧹 Cleaning Up Duplicate Diagrams")
    logger.info("=" * 80)
    
    engine = create_async_engine(
        settings.ASYNC_DATABASE_URL,
        echo=False,
        future=True
    )
    
    async_session = sessionmaker(
        engine, 
        class_=AsyncSession, 
        expire_on_commit=False
    )
    
    try:
        async with async_session() as session:
            # Find duplicates using raw SQL for clarity
            logger.info("Finding duplicate diagrams...")
            
            result = await session.execute(text("""
                SELECT model_id, name, COUNT(*) as count
                FROM diagrams
                GROUP BY model_id, name
                HAVING COUNT(*) > 1
            """))
            
            duplicates = result.fetchall()
            
            if not duplicates:
                logger.info("✅ No duplicate diagrams found!")
                return True
            
            logger.info(f"Found {len(duplicates)} sets of duplicate diagrams")
            
            total_deleted = 0
            
            # For each set of duplicates, keep the oldest and delete the rest
            for row in duplicates:
                model_id = row[0]
                name = row[1]
                count = row[2]
                
                logger.info(f"\nProcessing duplicates:")
                logger.info(f"  Model ID: {model_id}")
                logger.info(f"  Name: '{name}'")
                logger.info(f"  Count: {count}")
                
                # Get all diagrams with this model_id and name, ordered by created_at
                result = await session.execute(
                    select(Diagram)
                    .where(Diagram.model_id == model_id, Diagram.name == name)
                    .order_by(Diagram.created_at.asc())
                )
                diagrams = result.scalars().all()
                
                if len(diagrams) > 1:
                    # Keep the first (oldest) one
                    keep_diagram = diagrams[0]
                    delete_diagrams = diagrams[1:]
                    
                    logger.info(f"  ✓ Keeping: {keep_diagram.id} (created {keep_diagram.created_at})")
                    
                    # Delete the rest
                    for diagram in delete_diagrams:
                        logger.info(f"  ✗ Deleting: {diagram.id} (created {diagram.created_at})")
                        await session.delete(diagram)
                        total_deleted += 1
            
            # Commit all deletions
            await session.commit()
            
            logger.info(f"\n✅ Deleted {total_deleted} duplicate diagrams")
            
        logger.info("\n" + "=" * 80)
        logger.info("✅ Cleanup completed successfully!")
        logger.info("=" * 80)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Cleanup failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await engine.dispose()


async def list_all_diagrams():
    """List all diagrams for verification"""
    
    logger.info("\n📋 Current Diagrams:")
    
    engine = create_async_engine(
        settings.ASYNC_DATABASE_URL,
        echo=False,
        future=True
    )
    
    async_session = sessionmaker(
        engine, 
        class_=AsyncSession, 
        expire_on_commit=False
    )
    
    try:
        async with async_session() as session:
            result = await session.execute(
                select(Diagram).order_by(Diagram.model_id, Diagram.name, Diagram.created_at)
            )
            diagrams = result.scalars().all()
            
            if not diagrams:
                logger.info("  (No diagrams found)")
                return
            
            current_model = None
            diagram_count = 0
            
            for diagram in diagrams:
                if current_model != diagram.model_id:
                    current_model = diagram.model_id
                    logger.info(f"\n  Model: {diagram.model_id}")
                
                logger.info(f"    - {diagram.name} (id={diagram.id}, created={diagram.created_at})")
                diagram_count += 1
            
            logger.info(f"\n  Total diagrams: {diagram_count}")
            
    finally:
        await engine.dispose()


async def show_duplicate_summary():
    """Show a summary of duplicates without deleting"""
    
    logger.info("\n" + "=" * 80)
    logger.info("📊 Duplicate Diagrams Summary")
    logger.info("=" * 80)
    
    engine = create_async_engine(
        settings.ASYNC_DATABASE_URL,
        echo=False,
        future=True
    )
    
    try:
        async with engine.begin() as conn:
            result = await conn.execute(text("""
                SELECT 
                    model_id, 
                    name, 
                    COUNT(*) as count,
                    MIN(created_at) as first_created,
                    MAX(created_at) as last_created
                FROM diagrams
                GROUP BY model_id, name
                HAVING COUNT(*) > 1
                ORDER BY count DESC, name
            """))
            
            duplicates = result.fetchall()
            
            if not duplicates:
                logger.info("\n✅ No duplicates found!")
                return
            
            logger.info(f"\nFound {len(duplicates)} sets of duplicates:\n")
            
            for row in duplicates:
                model_id, name, count, first_created, last_created = row
                logger.info(f"  Model: {model_id}")
                logger.info(f"  Name: '{name}'")
                logger.info(f"  Duplicates: {count}")
                logger.info(f"  First created: {first_created}")
                logger.info(f"  Last created: {last_created}")
                logger.info("")
                
    finally:
        await engine.dispose()


async def main():
    """Main cleanup function"""
    
    # Show current state
    await list_all_diagrams()
    
    # Show duplicate summary
    await show_duplicate_summary()
    
    # Ask for confirmation
    logger.info("\n" + "=" * 80)
    response = input("Do you want to delete duplicate diagrams? (yes/no): ")
    
    if response.lower() not in ['yes', 'y']:
        logger.info("❌ Cleanup cancelled")
        return False
    
    # Cleanup duplicates
    success = await cleanup_duplicates()
    
    if success:
        # Show final state
        await list_all_diagrams()
    
    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)