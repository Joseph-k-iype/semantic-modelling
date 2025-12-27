"""
Workspace Repository
"""
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workspace import Workspace
from app.repositories.base import BaseRepository


class WorkspaceRepository(BaseRepository[Workspace]):
    """Repository for workspace operations"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(Workspace, db)
    
    async def get_by_user(self, user_id: str) -> List[Workspace]:
        """Get all workspaces for a user"""
        result = await self.db.execute(
            select(Workspace)
            .where(Workspace.created_by == user_id)
            .order_by(Workspace.created_at.desc())
        )
        return list(result.scalars().all())