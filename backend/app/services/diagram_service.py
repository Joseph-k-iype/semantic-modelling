# backend/app/services/diagram_service.py
"""
Diagram Service - Enhanced with semantic graph synchronization
UPDATED: Consistent layout creation, no duplication
Path: backend/app/services/diagram_service.py
"""
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models.diagram import Diagram
from app.models.layout import Layout
from app.repositories.diagram_repository import DiagramRepository
from app.repositories.layout_repository import LayoutRepository
from app.services.semantic_model_service import SemanticModelService
from app.schemas.diagram import DiagramCreate, DiagramUpdate
import structlog
import uuid

logger = structlog.get_logger()


class DiagramService:
    """Service for managing diagrams"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.diagram_repo = DiagramRepository(db)
        self.layout_repo = LayoutRepository(db)
        self.semantic_service = SemanticModelService()
    
    async def create_diagram(
        self,
        user_id: str,
        diagram_data: DiagramCreate
    ) -> Diagram:
        """
        Create a new diagram
        
        Args:
            user_id: ID of the user creating the diagram
            diagram_data: Diagram creation data
            
        Returns:
            Created diagram
        """
        try:
            # Create diagram
            diagram_dict = {
                "id": str(uuid.uuid4()),
                "name": diagram_data.name,
                "type": diagram_data.type,
                "model_id": diagram_data.model_id,
                "description": diagram_data.description,
                "nodes": [],
                "edges": [],
                "created_by": user_id,
                "updated_by": user_id
            }
            
            diagram = await self.diagram_repo.create(diagram_dict)
            
            # Create default layout
            # NOTE: This is now handled explicitly, not by database trigger
            layout_dict = {
                "id": str(uuid.uuid4()),
                "diagram_id": str(diagram.id),
                "name": "Default Layout",
                "layout_engine": "manual",
                "layout_data": {
                    "nodes": {},
                    "edges": {},
                    "constraints": {},
                    "viewport": {
                        "x": 0,
                        "y": 0,
                        "zoom": 1.0
                    }
                },
                "is_default": True,
                "created_by": user_id
            }
            
            await self.layout_repo.create(layout_dict)
            
            logger.info(
                "Diagram created with default layout",
                diagram_id=str(diagram.id),
                user_id=user_id,
                type=diagram.type
            )
            
            return diagram
            
        except Exception as e:
            logger.error(
                "Failed to create diagram",
                user_id=user_id,
                diagram_name=diagram_data.name,
                error=str(e)
            )
            raise
    
    async def update_diagram(
        self,
        diagram_id: str,
        user_id: str,
        update_data: DiagramUpdate
    ) -> Diagram:
        """
        Update diagram and sync to semantic graph
        
        Args:
            diagram_id: Diagram ID
            user_id: ID of the user updating
            update_data: Update data
            
        Returns:
            Updated diagram
        """
        try:
            # Get existing diagram
            diagram = await self.diagram_repo.get(diagram_id)
            if not diagram:
                raise ValueError(f"Diagram {diagram_id} not found")
            
            # Update diagram
            update_dict = update_data.model_dump(exclude_unset=True)
            update_dict["updated_by"] = user_id
            
            diagram = await self.diagram_repo.update(diagram_id, update_dict)
            
            # Sync to semantic graph if nodes or edges changed
            if "nodes" in update_dict or "edges" in update_dict:
                try:
                    sync_stats = await self.semantic_service.sync_diagram_to_graph(
                        self.db,
                        diagram_id,
                        user_id,
                        diagram.nodes,
                        diagram.edges
                    )
                    
                    logger.info(
                        "Diagram synced to semantic graph",
                        diagram_id=diagram_id,
                        sync_stats=sync_stats
                    )
                except Exception as sync_error:
                    # Log but don't fail the update
                    logger.warning(
                        "Failed to sync diagram to graph",
                        diagram_id=diagram_id,
                        error=str(sync_error)
                    )
            
            logger.info(
                "Diagram updated",
                diagram_id=diagram_id,
                user_id=user_id
            )
            
            return diagram
            
        except Exception as e:
            logger.error(
                "Failed to update diagram",
                diagram_id=diagram_id,
                user_id=user_id,
                error=str(e)
            )
            raise
    
    async def get_diagram(self, diagram_id: str) -> Optional[Diagram]:
        """
        Get diagram by ID
        
        Args:
            diagram_id: Diagram ID
            
        Returns:
            Diagram or None
        """
        return await self.diagram_repo.get(diagram_id)
    
    async def get_diagrams_by_model(
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
        return await self.diagram_repo.get_by_model(model_id, skip, limit)
    
    async def get_diagrams_by_workspace(
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
        return await self.diagram_repo.get_by_workspace(workspace_id, skip, limit)
    
    async def delete_diagram(self, diagram_id: str) -> bool:
        """
        Soft delete a diagram
        
        Args:
            diagram_id: Diagram ID
            
        Returns:
            True if deleted, False if not found
        """
        try:
            result = await self.diagram_repo.soft_delete(diagram_id)
            
            if result:
                logger.info(
                    "Diagram deleted",
                    diagram_id=diagram_id
                )
            else:
                logger.warning(
                    "Diagram not found for deletion",
                    diagram_id=diagram_id
                )
            
            return result
            
        except Exception as e:
            logger.error(
                "Failed to delete diagram",
                diagram_id=diagram_id,
                error=str(e)
            )
            raise
    
    async def duplicate_diagram(
        self,
        diagram_id: str,
        user_id: str,
        new_name: str,
        copy_layouts: bool = True,
        target_model_id: Optional[str] = None
    ) -> Diagram:
        """
        Duplicate a diagram
        
        Args:
            diagram_id: Source diagram ID
            user_id: ID of the user duplicating
            new_name: Name for the new diagram
            copy_layouts: Whether to copy layouts
            target_model_id: Target model ID (if different from source)
            
        Returns:
            New diagram
        """
        try:
            # Get source diagram
            source = await self.diagram_repo.get(diagram_id)
            if not source:
                raise ValueError(f"Source diagram {diagram_id} not found")
            
            # Create new diagram
            new_diagram_dict = {
                "id": str(uuid.uuid4()),
                "name": new_name,
                "type": source.type,
                "model_id": target_model_id or str(source.model_id),
                "description": f"Copy of {source.name}",
                "nodes": source.nodes.copy() if source.nodes else [],
                "edges": source.edges.copy() if source.edges else [],
                "created_by": user_id,
                "updated_by": user_id
            }
            
            new_diagram = await self.diagram_repo.create(new_diagram_dict)
            
            # Copy layouts if requested
            if copy_layouts:
                source_layouts = await self.layout_repo.get_by_diagram(diagram_id)
                
                for source_layout in source_layouts:
                    layout_dict = {
                        "id": str(uuid.uuid4()),
                        "diagram_id": str(new_diagram.id),
                        "name": source_layout.name,
                        "layout_engine": source_layout.layout_engine,
                        "layout_data": source_layout.layout_data.copy() if source_layout.layout_data else {},
                        "is_default": source_layout.is_default,
                        "created_by": user_id
                    }
                    
                    await self.layout_repo.create(layout_dict)
            else:
                # Create default layout
                layout_dict = {
                    "id": str(uuid.uuid4()),
                    "diagram_id": str(new_diagram.id),
                    "name": "Default Layout",
                    "layout_engine": "manual",
                    "layout_data": {
                        "nodes": {},
                        "edges": {},
                        "constraints": {},
                        "viewport": {
                            "x": 0,
                            "y": 0,
                            "zoom": 1.0
                        }
                    },
                    "is_default": True,
                    "created_by": user_id
                }
                
                await self.layout_repo.create(layout_dict)
            
            logger.info(
                "Diagram duplicated",
                source_diagram_id=diagram_id,
                new_diagram_id=str(new_diagram.id),
                user_id=user_id,
                copy_layouts=copy_layouts
            )
            
            return new_diagram
            
        except Exception as e:
            logger.error(
                "Failed to duplicate diagram",
                diagram_id=diagram_id,
                user_id=user_id,
                error=str(e)
            )
            raise
    
    async def get_diagram_with_layouts(self, diagram_id: str) -> Optional[Dict[str, Any]]:
        """
        Get diagram with all its layouts
        
        Args:
            diagram_id: Diagram ID
            
        Returns:
            Dictionary with diagram and layouts, or None
        """
        try:
            diagram = await self.diagram_repo.get(diagram_id)
            if not diagram:
                return None
            
            layouts = await self.layout_repo.get_by_diagram(diagram_id)
            
            return {
                "diagram": diagram,
                "layouts": layouts,
                "default_layout": next(
                    (layout for layout in layouts if layout.is_default),
                    layouts[0] if layouts else None
                )
            }
            
        except Exception as e:
            logger.error(
                "Failed to get diagram with layouts",
                diagram_id=diagram_id,
                error=str(e)
            )
            raise