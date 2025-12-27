# backend/app/services/diagram_service.py
"""
Diagram Service - Enhanced with semantic graph synchronization
"""
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
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
        # Create diagram
        diagram = await self.diagram_repo.create({
            "id": str(uuid.uuid4()),
            "name": diagram_data.name,
            "type": diagram_data.type,
            "model_id": diagram_data.model_id,
            "description": diagram_data.description,
            "nodes": [],
            "edges": [],
            "created_by": user_id,
            "updated_by": user_id
        })
        
        # Create default layout
        await self.layout_repo.create({
            "id": str(uuid.uuid4()),
            "diagram_id": diagram.id,
            "name": "Default Layout",
            "algorithm": "manual",
            "layout_data": {
                "nodes": [],
                "direction": "TB",
                "spacing": {"node": [80, 80], "rank": 80}
            },
            "is_default": True,
            "created_by": user_id
        })
        
        logger.info(
            "Diagram created",
            diagram_id=diagram.id,
            user_id=user_id,
            type=diagram.type
        )
        
        return diagram
    
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
                    "Diagram synced to graph",
                    diagram_id=diagram_id,
                    stats=sync_stats
                )
            except Exception as e:
                logger.error(
                    "Failed to sync diagram to graph",
                    diagram_id=diagram_id,
                    error=str(e)
                )
                # Don't fail the update if graph sync fails
        
        return diagram
    
    async def save_diagram(
        self,
        diagram_id: str,
        user_id: str,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
        viewport: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Save diagram state (nodes, edges, viewport)
        
        Args:
            diagram_id: Diagram ID
            user_id: User ID
            nodes: List of nodes
            edges: List of edges
            viewport: Viewport state
            
        Returns:
            Save result with statistics
        """
        # Update diagram
        diagram = await self.diagram_repo.update(diagram_id, {
            "nodes": nodes,
            "edges": edges,
            "viewport": viewport or {"x": 0, "y": 0, "zoom": 1},
            "updated_by": user_id
        })
        
        # Sync to semantic graph
        sync_stats = await self.semantic_service.sync_diagram_to_graph(
            self.db,
            diagram_id,
            user_id,
            nodes,
            edges
        )
        
        return {
            "diagram_id": diagram.id,
            "saved_at": diagram.updated_at.isoformat() if diagram.updated_at else None,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "sync_stats": sync_stats
        }
    
    async def get_diagram(self, diagram_id: str) -> Optional[Diagram]:
        """Get diagram by ID"""
        return await self.diagram_repo.get(diagram_id)
    
    async def get_diagrams_by_model(
        self,
        model_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Diagram]:
        """Get all diagrams for a model"""
        return await self.diagram_repo.get_by_model(model_id, skip, limit)
    
    async def delete_diagram(self, diagram_id: str) -> bool:
        """Delete a diagram"""
        return await self.diagram_repo.delete(diagram_id)
    
    async def get_diagram_lineage(
        self,
        diagram_id: str,
        user_id: str,
        node_id: str,
        direction: str = "both"
    ) -> List[Dict[str, Any]]:
        """Get lineage for a node in the diagram"""
        diagram = await self.diagram_repo.get(diagram_id)
        if not diagram:
            raise ValueError(f"Diagram {diagram_id} not found")
        
        return await self.semantic_service.get_lineage(
            user_id,
            diagram.model_id,
            node_id,
            direction
        )
    
    async def get_impact_analysis(
        self,
        diagram_id: str,
        user_id: str,
        node_id: str
    ) -> Dict[str, Any]:
        """Get impact analysis for a node"""
        diagram = await self.diagram_repo.get(diagram_id)
        if not diagram:
            raise ValueError(f"Diagram {diagram_id} not found")
        
        return await self.semantic_service.get_impact_analysis(
            user_id,
            diagram.model_id,
            node_id
        )