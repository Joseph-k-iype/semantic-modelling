# backend/app/repositories/base.py
"""
Base Repository with Common CRUD Operations
"""
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import DeclarativeMeta

ModelType = TypeVar("ModelType", bound=DeclarativeMeta)


class BaseRepository(Generic[ModelType]):
    """Base repository with common CRUD operations"""
    
    def __init__(self, model: Type[ModelType], db: AsyncSession):
        """
        Initialize repository
        
        Args:
            model: SQLAlchemy model class
            db: Async database session
        """
        self.model = model
        self.db = db
    
    async def get(self, id: str) -> Optional[ModelType]:
        """
        Get single record by ID
        
        Args:
            id: Record ID
            
        Returns:
            Model instance or None
        """
        result = await self.db.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()
    
    async def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        **filters
    ) -> List[ModelType]:
        """
        Get multiple records with pagination
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            **filters: Additional filter conditions
            
        Returns:
            List of model instances
        """
        query = select(self.model)
        
        # Apply filters
        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.where(getattr(self.model, key) == value)
        
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def create(self, data: Dict[str, Any]) -> ModelType:
        """
        Create new record
        
        Args:
            data: Dictionary of model attributes
            
        Returns:
            Created model instance
        """
        instance = self.model(**data)
        self.db.add(instance)
        await self.db.commit()
        await self.db.refresh(instance)
        return instance
    
    async def update(
        self,
        id: str,
        data: Dict[str, Any]
    ) -> Optional[ModelType]:
        """
        Update existing record
        
        Args:
            id: Record ID
            data: Dictionary of attributes to update
            
        Returns:
            Updated model instance or None
        """
        # Remove None values
        data = {k: v for k, v in data.items() if v is not None}
        
        if not data:
            return await self.get(id)
        
        stmt = (
            update(self.model)
            .where(self.model.id == id)
            .values(**data)
            .returning(self.model)
        )
        
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.scalar_one_or_none()
    
    async def delete(self, id: str) -> bool:
        """
        Delete record
        
        Args:
            id: Record ID
            
        Returns:
            True if deleted, False if not found
        """
        result = await self.db.execute(
            delete(self.model).where(self.model.id == id)
        )
        await self.db.commit()
        return result.rowcount > 0
    
    async def count(self, **filters) -> int:
        """
        Count records matching filters
        
        Args:
            **filters: Filter conditions
            
        Returns:
            Number of matching records
        """
        from sqlalchemy import func
        
        query = select(func.count()).select_from(self.model)
        
        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.where(getattr(self.model, key) == value)
        
        result = await self.db.execute(query)
        return result.scalar_one()