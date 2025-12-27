"""
Version Repository
"""
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.version import Version
from app.repositories.base import BaseRepository


class VersionRepository(BaseRepository[Version]):
    """Repository for version operations"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(Version, db)
    
    async def get_by_entity(
        self,
        entity_type: str,
        entity_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Version]:
        """Get all versions for an entity"""
        result = await self.db.execute(
            select(Version)
            .where(Version.entity_type == entity_type)
            .where(Version.entity_id == entity_id)
            .offset(skip)
            .limit(limit)
            .order_by(Version.version_number.desc())
        )
        return list(result.scalars().all())
    
    async def get_latest_version(
        self,
        entity_type: str,
        entity_id: str
    ) -> Optional[Version]:
        """Get the latest version for an entity"""
        result = await self.db.execute(
            select(Version)
            .where(Version.entity_type == entity_type)
            .where(Version.entity_id == entity_id)
            .order_by(Version.version_number.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()