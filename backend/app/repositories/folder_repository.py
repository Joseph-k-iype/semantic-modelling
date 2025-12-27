"""
Folder Repository
"""
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.folder import Folder
from app.repositories.base import BaseRepository


class FolderRepository(BaseRepository[Folder]):
    """Repository for folder operations"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(Folder, db)
    
    async def get_by_workspace(
        self,
        workspace_id: str,
        parent_id: Optional[str] = None
    ) -> List[Folder]:
        """Get folders in a workspace, optionally filtered by parent"""
        query = select(Folder).where(Folder.workspace_id == workspace_id)
        
        if parent_id:
            query = query.where(Folder.parent_folder_id == parent_id)
        else:
            query = query.where(Folder.parent_folder_id.is_(None))
        
        result = await self.db.execute(query.order_by(Folder.name))
        return list(result.scalars().all())