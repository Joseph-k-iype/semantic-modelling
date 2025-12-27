# backend/app/api/v1/endpoints/diagrams.py
"""
Diagram API Endpoints - FIXED for development (no auth required)
"""
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.diagram import (
    DiagramCreate,
    DiagramUpdate,
    DiagramResponse,
    DiagramSaveRequest,
    DiagramLineageRequest,
    DiagramLineageResponse
)
from app.services.diagram_service import DiagramService
import structlog
import uuid

logger = structlog.get_logger()
router = APIRouter()


# TEMPORARY: Mock user ID for development
# TODO: Replace with actual authentication
def get_mock_user_id() -> str:
    """Get mock user ID for development - replace with actual auth"""
    return "dev-user-" + str(uuid.uuid4())[:8]


@router.post("/", response_model=DiagramResponse, status_code=status.HTTP_201_CREATED)
async def create_diagram(
    *,
    db: AsyncSession = Depends(get_db),
    diagram_in: DiagramCreate
) -> Any:
    """
    Create a new diagram
    """
    diagram_service = DiagramService(db)
    user_id = get_mock_user_id()  # FIXED: Use mock user for now
    
    try:
        diagram = await diagram_service.create_diagram(
            user_id=user_id,
            diagram_data=diagram_in
        )
        logger.info("Diagram created successfully", diagram_id=diagram.id)
        return diagram
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
    diagram_id: str
) -> Any:
    """
    Get diagram by ID
    """
    diagram_service = DiagramService(db)
    
    diagram = await diagram_service.get_diagram(diagram_id)
    if not diagram:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Diagram {diagram_id} not found"
        )
    
    logger.info("Diagram retrieved", diagram_id=diagram_id)
    return diagram


@router.get("/model/{model_id}", response_model=List[DiagramResponse])
async def get_diagrams_by_model(
    *,
    db: AsyncSession = Depends(get_db),
    model_id: str,
    skip: int = 0,
    limit: int = 100
) -> Any:
    """
    Get all diagrams for a model
    """
    diagram_service = DiagramService(db)
    
    diagrams = await diagram_service.get_diagrams_by_model(
        model_id=model_id,
        skip=skip,
        limit=limit
    )
    
    logger.info("Diagrams retrieved for model", model_id=model_id, count=len(diagrams))
    return diagrams


@router.put("/{diagram_id}", response_model=DiagramResponse)
async def update_diagram(
    *,
    db: AsyncSession = Depends(get_db),
    diagram_id: str,
    diagram_in: DiagramUpdate
) -> Any:
    """
    Update diagram
    """
    diagram_service = DiagramService(db)
    user_id = get_mock_user_id()  # FIXED: Use mock user for now
    
    try:
        diagram = await diagram_service.update_diagram(
            diagram_id=diagram_id,
            user_id=user_id,
            update_data=diagram_in
        )
        logger.info("Diagram updated successfully", diagram_id=diagram_id)
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
    diagram_id: str,
    save_data: DiagramSaveRequest
) -> Any:
    """
    Save diagram state (nodes, edges, viewport) and sync to semantic graph
    
    This is the main save endpoint that:
    1. Saves diagram data to PostgreSQL
    2. Syncs entities/classes to FalkorDB graph database
    3. Returns sync statistics
    """
    diagram_service = DiagramService(db)
    user_id = get_mock_user_id()  # FIXED: Use mock user for now
    
    try:
        logger.info(
            "Saving diagram",
            diagram_id=diagram_id,
            node_count=len(save_data.nodes),
            edge_count=len(save_data.edges)
        )
        
        result = await diagram_service.save_diagram(
            diagram_id=diagram_id,
            user_id=user_id,
            nodes=save_data.nodes,
            edges=save_data.edges,
            viewport=save_data.viewport
        )
        
        logger.info(
            "Diagram saved successfully",
            diagram_id=diagram_id,
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
    diagram_id: str
) -> None:
    """
    Delete diagram
    """
    diagram_service = DiagramService(db)
    
    success = await diagram_service.delete_diagram(diagram_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Diagram {diagram_id} not found"
        )
    
    logger.info("Diagram deleted", diagram_id=diagram_id)


@router.post("/{diagram_id}/lineage", response_model=DiagramLineageResponse)
async def get_node_lineage(
    *,
    db: AsyncSession = Depends(get_db),
    diagram_id: str,
    lineage_request: DiagramLineageRequest
) -> Any:
    """
    Get lineage (upstream/downstream) for a node in the diagram
    """
    diagram_service = DiagramService(db)
    user_id = get_mock_user_id()  # FIXED: Use mock user for now
    
    try:
        lineage = await diagram_service.get_diagram_lineage(
            diagram_id=diagram_id,
            user_id=user_id,
            node_id=lineage_request.node_id,
            direction=lineage_request.direction
        )
        
        return DiagramLineageResponse(
            node_id=lineage_request.node_id,
            direction=lineage_request.direction,
            lineage=lineage
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Failed to get lineage", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get lineage: {str(e)}"
        )


@router.get("/{diagram_id}/validation")
async def validate_diagram(
    *,
    db: AsyncSession = Depends(get_db),
    diagram_id: str
) -> Any:
    """
    Validate diagram against notation rules
    """
    diagram_service = DiagramService(db)
    
    try:
        diagram = await diagram_service.get_diagram(diagram_id)
        if not diagram:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Diagram {diagram_id} not found"
            )
        
        # TODO: Implement validation logic
        return {
            "valid": True,
            "errors": [],
            "warnings": [],
            "info": []
        }
    except Exception as e:
        logger.error("Failed to validate diagram", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate diagram: {str(e)}"
        )