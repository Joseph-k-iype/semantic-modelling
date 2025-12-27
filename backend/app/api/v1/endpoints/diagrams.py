# backend/app/api/v1/endpoints/diagrams.py
"""
Diagram API Endpoints
"""
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
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

logger = structlog.get_logger()
router = APIRouter()


@router.post("/", response_model=DiagramResponse, status_code=status.HTTP_201_CREATED)
async def create_diagram(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    diagram_in: DiagramCreate
) -> Any:
    """
    Create a new diagram
    """
    diagram_service = DiagramService(db)
    
    try:
        diagram = await diagram_service.create_diagram(
            user_id=str(current_user.id),
            diagram_data=diagram_in
        )
        return diagram
    except Exception as e:
        logger.error("Failed to create diagram", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create diagram: {str(e)}"
        )


@router.get("/{diagram_id}", response_model=DiagramResponse)
async def get_diagram(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
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
    
    return diagram


@router.get("/model/{model_id}", response_model=List[DiagramResponse])
async def get_diagrams_by_model(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
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
    
    return diagrams


@router.put("/{diagram_id}", response_model=DiagramResponse)
async def update_diagram(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    diagram_id: str,
    diagram_in: DiagramUpdate
) -> Any:
    """
    Update diagram
    """
    diagram_service = DiagramService(db)
    
    try:
        diagram = await diagram_service.update_diagram(
            diagram_id=diagram_id,
            user_id=str(current_user.id),
            update_data=diagram_in
        )
        return diagram
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Failed to update diagram", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update diagram: {str(e)}"
        )


@router.post("/{diagram_id}/save")
async def save_diagram(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    diagram_id: str,
    save_data: DiagramSaveRequest
) -> Any:
    """
    Save diagram state (nodes, edges, viewport) and sync to semantic graph
    """
    diagram_service = DiagramService(db)
    
    try:
        result = await diagram_service.save_diagram(
            diagram_id=diagram_id,
            user_id=str(current_user.id),
            nodes=save_data.nodes,
            edges=save_data.edges,
            viewport=save_data.viewport
        )
        return result
    except Exception as e:
        logger.error("Failed to save diagram", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save diagram: {str(e)}"
        )


@router.delete("/{diagram_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_diagram(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
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


@router.post("/{diagram_id}/lineage", response_model=DiagramLineageResponse)
async def get_node_lineage(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    diagram_id: str,
    lineage_request: DiagramLineageRequest
) -> Any:
    """
    Get lineage (upstream/downstream) for a node in the diagram
    """
    diagram_service = DiagramService(db)
    
    try:
        lineage = await diagram_service.get_diagram_lineage(
            diagram_id=diagram_id,
            user_id=str(current_user.id),
            node_id=lineage_request.node_id,
            direction=lineage_request.direction
        )
        
        return {
            "node_id": lineage_request.node_id,
            "direction": lineage_request.direction,
            "lineage": lineage
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Failed to get lineage", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get lineage: {str(e)}"
        )


@router.post("/{diagram_id}/impact/{node_id}")
async def get_node_impact(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    diagram_id: str,
    node_id: str
) -> Any:
    """
    Get impact analysis for a node
    """
    diagram_service = DiagramService(db)
    
    try:
        impact = await diagram_service.get_impact_analysis(
            diagram_id=diagram_id,
            user_id=str(current_user.id),
            node_id=node_id
        )
        
        return {
            "node_id": node_id,
            "impact": impact
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Failed to get impact analysis", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get impact analysis: {str(e)}"
        )