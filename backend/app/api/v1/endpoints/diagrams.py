# backend/app/api/v1/endpoints/diagrams.py
"""
Diagram endpoints - FIXED with proper authentication
"""
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.diagram import (
    DiagramCreate,
    DiagramUpdate,
    DiagramResponse,
    DiagramSaveRequest
)
from app.services.diagram_service import DiagramService

logger = structlog.get_logger()

router = APIRouter()


@router.post("/", response_model=DiagramResponse, status_code=status.HTTP_201_CREATED)
async def create_diagram(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),  # FIXED: Require authentication
    diagram_in: DiagramCreate
) -> Any:
    """
    Create new diagram - REQUIRES AUTHENTICATION
    """
    diagram_service = DiagramService(db)
    
    try:
        diagram = await diagram_service.create_diagram(
            model_id=diagram_in.model_id,
            user_id=str(current_user.id),  # FIXED: Use actual user ID
            diagram_data=diagram_in
        )
        logger.info(
            "Diagram created successfully",
            diagram_id=diagram.id,
            user_id=str(current_user.id),
            type=diagram.type
        )
        return diagram
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Failed to create diagram", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create diagram: {str(e)}"
        )


@router.get("/{diagram_id}", response_model=DiagramResponse)
async def get_diagram(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),  # FIXED: Require authentication
    diagram_id: str
) -> Any:
    """
    Get diagram by ID - REQUIRES AUTHENTICATION
    """
    diagram_service = DiagramService(db)
    
    try:
        diagram = await diagram_service.get_diagram(diagram_id)
        
        if not diagram:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Diagram {diagram_id} not found"
            )
        
        # TODO: Check if user has access to this diagram's workspace
        logger.info("Diagram retrieved", diagram_id=diagram_id, user_id=str(current_user.id))
        return diagram
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get diagram", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve diagram: {str(e)}"
        )


@router.get("/model/{model_id}", response_model=List[DiagramResponse])
async def get_diagrams_by_model(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),  # FIXED: Require authentication
    model_id: str
) -> Any:
    """
    Get all diagrams for a model - REQUIRES AUTHENTICATION
    """
    diagram_service = DiagramService(db)
    
    try:
        diagrams = await diagram_service.get_diagrams_by_model(model_id)
        logger.info(
            "Diagrams retrieved for model",
            model_id=model_id,
            user_id=str(current_user.id),
            count=len(diagrams)
        )
        return diagrams
    except Exception as e:
        logger.error("Failed to get diagrams", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve diagrams: {str(e)}"
        )


@router.put("/{diagram_id}", response_model=DiagramResponse)
async def update_diagram(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),  # FIXED: Require authentication
    diagram_id: str,
    diagram_in: DiagramUpdate
) -> Any:
    """
    Update diagram - REQUIRES AUTHENTICATION
    """
    diagram_service = DiagramService(db)
    
    try:
        diagram = await diagram_service.update_diagram(
            diagram_id=diagram_id,
            user_id=str(current_user.id),  # FIXED: Use actual user ID
            update_data=diagram_in
        )
        logger.info(
            "Diagram updated successfully",
            diagram_id=diagram_id,
            user_id=str(current_user.id)
        )
        return diagram
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Failed to update diagram", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update diagram: {str(e)}"
        )


@router.post("/{diagram_id}/save")
async def save_diagram(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),  # FIXED: Require authentication
    diagram_id: str,
    save_data: DiagramSaveRequest
) -> Any:
    """
    Save diagram state (nodes, edges, viewport) and sync to semantic graph
    
    REQUIRES AUTHENTICATION
    
    This endpoint:
    1. Saves diagram data to PostgreSQL
    2. Syncs entities/classes to FalkorDB graph database
    3. Returns sync statistics
    """
    diagram_service = DiagramService(db)
    
    try:
        logger.info(
            "Saving diagram",
            diagram_id=diagram_id,
            user_id=str(current_user.id),
            node_count=len(save_data.nodes),
            edge_count=len(save_data.edges)
        )
        
        result = await diagram_service.save_diagram(
            diagram_id=diagram_id,
            user_id=str(current_user.id),  # FIXED: Use actual user ID
            nodes=save_data.nodes,
            edges=save_data.edges,
            viewport=save_data.viewport
        )
        
        logger.info(
            "Diagram saved successfully",
            diagram_id=diagram_id,
            user_id=str(current_user.id),
            sync_stats=result.get("sync_stats", {})
        )
        
        return {
            "success": True,
            "message": "Diagram saved successfully",
            "diagram_id": result.get("diagram_id"),
            "saved_at": result.get("saved_at"),
            "sync_stats": result.get("sync_stats", {}),
            "node_count": result.get("node_count", 0),
            "edge_count": result.get("edge_count", 0)
        }
    except Exception as e:
        logger.error(
            "Failed to save diagram",
            diagram_id=diagram_id,
            user_id=str(current_user.id),
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save diagram: {str(e)}"
        )


@router.delete("/{diagram_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_diagram(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),  # FIXED: Require authentication
    diagram_id: str
) -> None:
    """
    Delete diagram - REQUIRES AUTHENTICATION
    """
    diagram_service = DiagramService(db)
    
    try:
        success = await diagram_service.delete_diagram(
            diagram_id=diagram_id,
            user_id=str(current_user.id)  # FIXED: Use actual user ID
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Diagram {diagram_id} not found"
            )
        
        logger.info(
            "Diagram deleted successfully",
            diagram_id=diagram_id,
            user_id=str(current_user.id)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete diagram", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete diagram: {str(e)}"
        )


@router.post("/{diagram_id}/lineage")
async def get_node_lineage(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),  # FIXED: Require authentication
    diagram_id: str,
    node_id: str,
    direction: str = "both",
    depth: int = 3
) -> Any:
    """
    Get lineage for a node in the diagram - REQUIRES AUTHENTICATION
    """
    diagram_service = DiagramService(db)
    
    try:
        lineage = await diagram_service.get_node_lineage(
            diagram_id=diagram_id,
            node_id=node_id,
            user_id=str(current_user.id),  # FIXED: Use actual user ID
            direction=direction,
            depth=depth
        )
        return lineage
        
    except Exception as e:
        logger.error("Failed to get lineage", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve lineage: {str(e)}"
        )


@router.post("/{diagram_id}/impact/{node_id}")
async def get_node_impact(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),  # FIXED: Require authentication
    diagram_id: str,
    node_id: str
) -> Any:
    """
    Get impact analysis for a node - REQUIRES AUTHENTICATION
    """
    diagram_service = DiagramService(db)
    
    try:
        impact = await diagram_service.get_node_impact(
            diagram_id=diagram_id,
            node_id=node_id,
            user_id=str(current_user.id)  # FIXED: Use actual user ID
        )
        return impact
        
    except Exception as e:
        logger.error("Failed to get impact", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve impact analysis: {str(e)}"
        )