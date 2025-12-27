# backend/app/repositories/diagram_repository.py
"""
Diagram Repository
"""
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.diagram import Diagram
from app.repositories.base import BaseRepository


class DiagramRepository(BaseRepository[Diagram]):
    """Repository for diagram operations"""
    
    def __init__(self, db: AsyncSession):
        """Initialize diagram repository"""
        super().__init__(Diagram, db)
    
    async def get_by_model(
        self,
        model_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Diagram]:
        """
        Get all diagrams for a model
        
        Args:
            model_id: Model ID
            skip: Number to skip
            limit: Maximum number to return
            
        Returns:
            List of diagrams
        """
        result = await self.db.execute(
            select(Diagram)
            .where(Diagram.model_id == model_id)
            .where(Diagram.deleted_at.is_(None))
            .offset(skip)
            .limit(limit)
            .order_by(Diagram.created_at.desc())
        )
        return list(result.scalars().all())
    
    async def get_by_workspace(
        self,
        workspace_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Diagram]:
        """
        Get all diagrams in a workspace
        
        Args:
            workspace_id: Workspace ID
            skip: Number to skip
            limit: Maximum number to return
            
        Returns:
            List of diagrams
        """
        result = await self.db.execute(
            select(Diagram)
            .where(Diagram.workspace_id == workspace_id)
            .where(Diagram.deleted_at.is_(None))
            .offset(skip)
            .limit(limit)
            .order_by(Diagram.created_at.desc())
        )
        return list(result.scalars().all())
    
    async def soft_delete(self, id: str) -> bool:
        """
        Soft delete a diagram
        
        Args:
            id: Diagram ID
            
        Returns:
            True if deleted, False if not found
        """
        from datetime import datetime
        
        diagram = await self.get(id)
        if not diagram:
            return False
        
        diagram.deleted_at = datetime.utcnow()
        await self.db.commit()
        return True