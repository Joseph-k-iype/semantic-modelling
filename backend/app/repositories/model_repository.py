"""
Model Repository
"""
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.model import Model
from app.repositories.base import BaseRepository


class ModelRepository(BaseRepository[Model]):
    """Repository for model operations"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(Model, db)
    
    async def get_by_workspace(
        self,
        workspace_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Model]:
        """Get all models in a workspace"""
        result = await self.db.execute(
            select(Model)
            .where(Model.workspace_id == workspace_id)
            .offset(skip)
            .limit(limit)
            .order_by(Model.created_at.desc())
        )
        return list(result.scalars().all())
    
    async def get_by_folder(
        self,
        folder_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Model]:
        """Get all models in a folder"""
        result = await self.db.execute(
            select(Model)
            .where(Model.folder_id == folder_id)
            .offset(skip)
            .limit(limit)
            .order_by(Model.created_at.desc())
        )
        return list(result.scalars().all())