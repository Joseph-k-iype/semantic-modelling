# backend/app/repositories/layout_repository.py
"""
Layout Repository
"""
from typing import List, Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.layout import Layout
from app.repositories.base import BaseRepository


class LayoutRepository(BaseRepository[Layout]):
    """Repository for layout operations"""
    
    def __init__(self, db: AsyncSession):
        """Initialize layout repository"""
        super().__init__(Layout, db)
    
    async def get_by_diagram(
        self,
        diagram_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Layout]:
        """
        Get all layouts for a diagram
        
        Args:
            diagram_id: Diagram ID
            skip: Number to skip
            limit: Maximum number to return
            
        Returns:
            List of layouts
        """
        result = await self.db.execute(
            select(Layout)
            .where(Layout.diagram_id == diagram_id)
            .where(Layout.deleted_at.is_(None))
            .offset(skip)
            .limit(limit)
            .order_by(Layout.is_default.desc(), Layout.created_at.desc())
        )
        return list(result.scalars().all())
    
    async def get_default(self, diagram_id: str) -> Optional[Layout]:
        """
        Get default layout for a diagram
        
        Args:
            diagram_id: Diagram ID
            
        Returns:
            Default layout or None
        """
        result = await self.db.execute(
            select(Layout)
            .where(Layout.diagram_id == diagram_id)
            .where(Layout.is_default == True)
            .where(Layout.deleted_at.is_(None))
            .limit(1)
        )
        return result.scalar_one_or_none()
    
    async def set_default(self, id: str, diagram_id: str) -> bool:
        """
        Set a layout as default (unsets others)
        
        Args:
            id: Layout ID to set as default
            diagram_id: Diagram ID
            
        Returns:
            True if successful
        """
        # Unset all defaults for this diagram
        await self.db.execute(
            update(Layout)
            .where(Layout.diagram_id == diagram_id)
            .values(is_default=False)
        )
        
        # Set this one as default
        await self.db.execute(
            update(Layout)
            .where(Layout.id == id)
            .values(is_default=True)
        )
        
        await self.db.commit()
        return True
    
    async def soft_delete(self, id: str) -> bool:
        """
        Soft delete a layout
        
        Args:
            id: Layout ID
            
        Returns:
            True if deleted, False if not found
        """
        from datetime import datetime
        
        layout = await self.get(id)
        if not layout:
            return False
        
        layout.deleted_at = datetime.utcnow()
        layout.is_active = False
        await self.db.commit()
        return True