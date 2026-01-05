# backend/app/api/v1/endpoints/diagrams.py
"""
Diagram API Endpoints - FIXED Routing Issue
Path: backend/app/api/v1/endpoints/diagrams.py

CRITICAL FIX: Changed @router.post("/") to @router.post("")
This creates endpoint at /diagrams instead of /diagrams/
"""

from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
import structlog

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.diagram import Diagram
from app.schemas.diagram import (
    DiagramCreate,
    DiagramUpdate,
    DiagramResponse,
    DiagramPublicResponse,
    DiagramListResponse,
)
from app.services.semantic_model_service import SemanticModelService

logger = structlog.get_logger()

router = APIRouter()


def get_semantic_service() -> SemanticModelService:
    """Dependency for semantic model service"""
    return SemanticModelService()


# CRITICAL FIX: Changed from "/" to "" to avoid trailing slash issue
@router.post("", response_model=DiagramResponse, status_code=status.HTTP_201_CREATED)
async def create_diagram(
    *,
    db: AsyncSession = Depends(get_db),
    diagram_in: DiagramCreate,
    current_user: User = Depends(get_current_user),
    semantic_service: SemanticModelService = Depends(get_semantic_service)
) -> Any:
    """
    Create new diagram
    Requires workspace_name and diagram_name
    Requires authentication
    """
    try:
        logger.info(
            "diagram_create_request",
            workspace=diagram_in.workspace_name,
            name=diagram_in.name,
            user_id=str(current_user.id),
            username=current_user.username
        )
        
        # Generate graph name using format: {workspace}/{diagram}/{user}
        graph_name = semantic_service.generate_graph_name(
            username=current_user.username or current_user.email.split('@')[0],
            workspace_name=diagram_in.workspace_name,
            diagram_name=diagram_in.name
        )
        
        logger.info(
            "generated_graph_name",
            graph_name=graph_name
        )
        
        # Create diagram record
        diagram = Diagram(
            name=diagram_in.name,
            description=diagram_in.description,
            workspace_name=diagram_in.workspace_name,
            graph_name=graph_name,
            notation='UML_CLASS',  # Always UML for Semantic Architect
            created_by=current_user.id,
            settings={
                "nodes": [node.dict() for node in diagram_in.nodes] if diagram_in.nodes else [],
                "edges": [edge.dict() for edge in diagram_in.edges] if diagram_in.edges else [],
                "viewport": diagram_in.viewport.dict() if diagram_in.viewport else {"x": 0, "y": 0, "zoom": 1}
            }
        )
        
        db.add(diagram)
        await db.commit()
        await db.refresh(diagram)
        
        logger.info(
            "diagram_created",
            diagram_id=str(diagram.id),
            name=diagram.name,
            workspace=diagram.workspace_name,
            graph_name=graph_name,
            user_id=str(current_user.id)
        )
        
        # Prepare response
        settings = diagram.settings or {}
        response_data = {
            "id": diagram.id,
            "name": diagram.name,
            "workspace_name": diagram.workspace_name,
            "description": diagram.description,
            "notation": diagram.notation,
            "graph_name": diagram.graph_name,
            "is_published": diagram.is_published,
            "published_at": diagram.published_at,
            "nodes": settings.get('nodes', []),
            "edges": settings.get('edges', []),
            "viewport": settings.get('viewport', {"x": 0, "y": 0, "zoom": 1}),
            "settings": settings,
            "created_at": diagram.created_at,
            "updated_at": diagram.updated_at,
            "created_by": diagram.created_by,
        }
        
        return response_data
        
    except Exception as e:
        await db.rollback()
        logger.error("diagram_creation_failed", error=str(e), error_type=type(e).__name__)
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create diagram: {str(e)}"
        )


@router.get("/published", response_model=List[DiagramPublicResponse])
async def get_published_diagrams(
    *,
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100
) -> Any:
    """
    Get all published diagrams for homepage display
    Includes computed statistics for each diagram
    No authentication required
    """
    try:
        # Query published diagrams with JOIN to users for author name
        query = select(
            Diagram,
            User.username.label('author_name')
        ).join(
            User, Diagram.created_by == User.id
        ).where(
            and_(
                Diagram.is_published == True,
                Diagram.deleted_at == None
            )
        ).order_by(
            Diagram.updated_at.desc()
        ).offset(skip).limit(limit)
        
        result = await db.execute(query)
        rows = result.all()
        
        # Build response with statistics
        diagrams = []
        for diagram, author_name in rows:
            # Count nodes and edges from settings
            settings = diagram.settings or {}
            nodes = settings.get('nodes', [])
            edges = settings.get('edges', [])
            
            # Count only class-like nodes (exclude packages)
            total_classes = sum(
                1 for node in nodes 
                if node.get('type') in ['class', 'interface', 'object', 'enumeration']
            )
            
            total_relationships = len(edges)
            
            diagrams.append({
                "id": diagram.id,
                "name": diagram.name,
                "workspace_name": diagram.workspace_name or "Default",
                "author_name": author_name,
                "total_classes": total_classes,
                "total_relationships": total_relationships,
                "created_at": diagram.created_at,
                "updated_at": diagram.updated_at,
            })
        
        return diagrams
        
    except Exception as e:
        logger.error("failed_to_fetch_published_diagrams", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch published diagrams: {str(e)}"
        )


@router.get("/{diagram_id}", response_model=DiagramResponse)
async def get_diagram(
    *,
    db: AsyncSession = Depends(get_db),
    diagram_id: str,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get diagram by ID
    Requires authentication
    """
    try:
        query = select(Diagram).where(
            and_(
                Diagram.id == diagram_id,
                Diagram.deleted_at == None
            )
        )
        result = await db.execute(query)
        diagram = result.scalar_one_or_none()
        
        if not diagram:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Diagram not found"
            )
        
        # Extract data from settings
        settings = diagram.settings or {}
        nodes = settings.get('nodes', [])
        edges = settings.get('edges', [])
        viewport = settings.get('viewport', {"x": 0, "y": 0, "zoom": 1})
        
        return {
            "id": diagram.id,
            "name": diagram.name,
            "workspace_name": diagram.workspace_name,
            "description": diagram.description,
            "notation": diagram.notation,
            "graph_name": diagram.graph_name,
            "is_published": diagram.is_published,
            "published_at": diagram.published_at,
            "nodes": nodes,
            "edges": edges,
            "viewport": viewport,
            "settings": settings,
            "created_at": diagram.created_at,
            "updated_at": diagram.updated_at,
            "created_by": diagram.created_by,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("failed_to_fetch_diagram", diagram_id=diagram_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch diagram: {str(e)}"
        )


@router.put("/{diagram_id}", response_model=DiagramResponse)
async def update_diagram(
    *,
    db: AsyncSession = Depends(get_db),
    diagram_id: str,
    diagram_in: DiagramUpdate,
    current_user: User = Depends(get_current_user),
    semantic_service: SemanticModelService = Depends(get_semantic_service)
) -> Any:
    """
    Update diagram
    Requires authentication
    """
    try:
        query = select(Diagram).where(
            and_(
                Diagram.id == diagram_id,
                Diagram.deleted_at == None
            )
        )
        result = await db.execute(query)
        diagram = result.scalar_one_or_none()
        
        if not diagram:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Diagram not found"
            )
        
        # Check ownership
        if diagram.created_by != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this diagram"
            )
        
        # Update fields
        if diagram_in.name is not None:
            diagram.name = diagram_in.name
        if diagram_in.description is not None:
            diagram.description = diagram_in.description
        
        # Update settings
        current_settings = diagram.settings or {}
        
        if diagram_in.nodes is not None:
            current_settings['nodes'] = [node.dict() for node in diagram_in.nodes]
        if diagram_in.edges is not None:
            current_settings['edges'] = [edge.dict() for edge in diagram_in.edges]
        if diagram_in.viewport is not None:
            current_settings['viewport'] = diagram_in.viewport.dict()
        if diagram_in.settings is not None:
            current_settings.update(diagram_in.settings)
        
        diagram.settings = current_settings
        diagram.updated_by = current_user.id
        
        await db.commit()
        await db.refresh(diagram)
        
        logger.info(
            "diagram_updated",
            diagram_id=str(diagram.id),
            user_id=str(current_user.id)
        )
        
        # Prepare response
        nodes = current_settings.get('nodes', [])
        edges = current_settings.get('edges', [])
        viewport = current_settings.get('viewport', {"x": 0, "y": 0, "zoom": 1})
        
        return {
            "id": diagram.id,
            "name": diagram.name,
            "workspace_name": diagram.workspace_name,
            "description": diagram.description,
            "notation": diagram.notation,
            "graph_name": diagram.graph_name,
            "is_published": diagram.is_published,
            "published_at": diagram.published_at,
            "nodes": nodes,
            "edges": edges,
            "viewport": viewport,
            "settings": current_settings,
            "created_at": diagram.created_at,
            "updated_at": diagram.updated_at,
            "created_by": diagram.created_by,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error("diagram_update_failed", diagram_id=diagram_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update diagram: {str(e)}"
        )


@router.post("/{diagram_id}/publish", status_code=status.HTTP_200_OK)
async def publish_diagram(
    *,
    db: AsyncSession = Depends(get_db),
    diagram_id: str,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Publish diagram to make it visible on homepage
    Requires authentication
    """
    try:
        query = select(Diagram).where(
            and_(
                Diagram.id == diagram_id,
                Diagram.deleted_at == None
            )
        )
        result = await db.execute(query)
        diagram = result.scalar_one_or_none()
        
        if not diagram:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Diagram not found"
            )
        
        # Check ownership
        if diagram.created_by != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to publish this diagram"
            )
        
        diagram.is_published = True
        diagram.published_at = func.now()
        diagram.updated_by = current_user.id
        
        await db.commit()
        
        logger.info(
            "diagram_published",
            diagram_id=str(diagram.id),
            user_id=str(current_user.id)
        )
        
        return {"message": "Diagram published successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error("diagram_publish_failed", diagram_id=diagram_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to publish diagram: {str(e)}"
        )


@router.delete("/{diagram_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_diagram(
    *,
    db: AsyncSession = Depends(get_db),
    diagram_id: str,
    current_user: User = Depends(get_current_user)
) -> None:
    """
    Soft delete diagram
    Requires authentication
    """
    try:
        from datetime import datetime
        
        query = select(Diagram).where(
            and_(
                Diagram.id == diagram_id,
                Diagram.deleted_at == None
            )
        )
        result = await db.execute(query)
        diagram = result.scalar_one_or_none()
        
        if not diagram:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Diagram not found"
            )
        
        # Check ownership
        if diagram.created_by != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this diagram"
            )
        
        diagram.deleted_at = datetime.utcnow()
        diagram.updated_by = current_user.id
        
        await db.commit()
        
        logger.info(
            "diagram_deleted",
            diagram_id=str(diagram.id),
            user_id=str(current_user.id)
        )
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error("diagram_delete_failed", diagram_id=diagram_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete diagram: {str(e)}"
        )