"""
Publish Workflow Repository
"""
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.publish_workflow import PublishWorkflow
from app.repositories.base import BaseRepository


class PublishRepository(BaseRepository[PublishWorkflow]):
    """Repository for publish workflow operations"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(PublishWorkflow, db)
    
    async def get_pending(self, skip: int = 0, limit: int = 100) -> List[PublishWorkflow]:
        """Get all pending publish requests"""
        result = await self.db.execute(
            select(PublishWorkflow)
            .where(PublishWorkflow.status == "pending")
            .offset(skip)
            .limit(limit)
            .order_by(PublishWorkflow.requested_at.desc())
        )
        return list(result.scalars().all())
    
    async def get_by_model(self, model_id: str) -> List[PublishWorkflow]:
        """Get all publish workflows for a model"""
        result = await self.db.execute(
            select(PublishWorkflow)
            .where(PublishWorkflow.model_id == model_id)
            .order_by(PublishWorkflow.requested_at.desc())
        )
        return list(result.scalars().all())