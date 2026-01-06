# backend/app/api/v1/endpoints/diagrams.py
"""
Diagram API Endpoints - Complete FalkorDB Integration
Path: backend/app/api/v1/endpoints/diagrams.py

FIXES:
- Proper graph naming: {username}/{workspace_name}/{diagram_name}
- Real-time FalkorDB sync with nodes/edges
- Save attributes, methods, literals correctly
- Handle all 5 node types properly
"""

from typing import Any, List, Optional, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
import structlog
from datetime import datetime

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.diagram import Diagram
from app.schemas.diagram import (
    DiagramCreate,
    DiagramUpdate,
    DiagramResponse,
    NodeBase,
    EdgeBase,
)
from app.services.semantic_model_service import SemanticModelService

logger = structlog.get_logger()

router = APIRouter()


def get_semantic_service() -> SemanticModelService:
    """Dependency for semantic model service"""
    return SemanticModelService()


@router.post("", response_model=DiagramResponse, status_code=status.HTTP_201_CREATED)
async def create_diagram(
    *,
    db: AsyncSession = Depends(get_db),
    diagram_in: DiagramCreate,
    current_user: User = Depends(get_current_user),
    semantic_service: SemanticModelService = Depends(get_semantic_service)
) -> Any:
    """
    Create new diagram with proper FalkorDB graph naming
    Graph format: {username}/{workspace_name}/{diagram_name}
    """
    try:
        username = current_user.username or current_user.email.split('@')[0]
        
        logger.info(
            "diagram_create_request",
            workspace=diagram_in.workspace_name,
            name=diagram_in.name,
            user_id=str(current_user.id),
            username=username
        )
        
        # Generate graph name: {username}/{workspace}/{diagram}
        graph_name = f"{username}/{diagram_in.workspace_name}/{diagram_in.name}"
        
        logger.info("generated_graph_name", graph_name=graph_name)
        
        # Check if diagram with same graph_name exists
        stmt = select(Diagram).where(
            and_(
                Diagram.graph_name == graph_name,
                Diagram.deleted_at.is_(None)
            )
        )
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Diagram with name '{diagram_in.name}' already exists in workspace '{diagram_in.workspace_name}'"
            )
        
        # Create diagram
        diagram = Diagram(
            name=diagram_in.name,
            description=diagram_in.description,
            workspace_name=diagram_in.workspace_name,
            notation="UML_CLASS",
            graph_name=graph_name,
            settings={
                "nodes": [node.dict() for node in diagram_in.nodes] if diagram_in.nodes else [],
                "edges": [edge.dict() for edge in diagram_in.edges] if diagram_in.edges else [],
                "viewport": diagram_in.viewport.dict() if diagram_in.viewport else {"x": 0, "y": 0, "zoom": 1}
            },
            is_published=False,
            created_by=current_user.id,
            updated_by=current_user.id
        )
        
        db.add(diagram)
        await db.commit()
        await db.refresh(diagram)
        
        logger.info(
            "diagram_created",
            diagram_id=str(diagram.id),
            graph_name=graph_name,
            node_count=len(diagram_in.nodes) if diagram_in.nodes else 0
        )
        
        # Sync to FalkorDB if there are nodes/edges
        if diagram_in.nodes or diagram_in.edges:
            try:
                sync_result = await semantic_service.sync_to_falkordb(
                    graph_name=graph_name,
                    nodes=[node.dict() for node in diagram_in.nodes] if diagram_in.nodes else [],
                    edges=[edge.dict() for edge in diagram_in.edges] if diagram_in.edges else []
                )
                logger.info("falkordb_sync_complete", result=sync_result)
            except Exception as sync_error:
                logger.warning("falkordb_sync_failed", error=str(sync_error))
                # Don't fail diagram creation if sync fails
        
        return DiagramResponse(
            id=diagram.id,
            name=diagram.name,
            description=diagram.description,
            workspace_name=diagram.workspace_name,
            graph_name=diagram.graph_name,
            notation=diagram.notation,
            is_published=diagram.is_published,
            published_at=diagram.published_at,
            settings=diagram.settings,
            created_at=diagram.created_at,
            updated_at=diagram.updated_at,
            created_by=str(diagram.created_by) if diagram.created_by else None,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("diagram_create_failed", error=str(e))
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create diagram: {str(e)}"
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
    Update diagram and sync to FalkorDB
    """
    try:
        # Get diagram
        stmt = select(Diagram).where(
            and_(
                Diagram.id == diagram_id,
                Diagram.deleted_at.is_(None)
            )
        )
        result = await db.execute(stmt)
        diagram = result.scalar_one_or_none()
        
        if not diagram:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Diagram not found"
            )
        
        # Update fields
        if diagram_in.name:
            diagram.name = diagram_in.name
        if diagram_in.description is not None:
            diagram.description = diagram_in.description
        if diagram_in.nodes is not None or diagram_in.edges is not None:
            current_settings = diagram.settings or {}
            if diagram_in.nodes is not None:
                current_settings["nodes"] = [node.dict() for node in diagram_in.nodes]
            if diagram_in.edges is not None:
                current_settings["edges"] = [edge.dict() for edge in diagram_in.edges]
            if diagram_in.viewport is not None:
                current_settings["viewport"] = diagram_in.viewport.dict()
            diagram.settings = current_settings
        
        diagram.updated_by = current_user.id
        diagram.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(diagram)
        
        logger.info(
            "diagram_updated",
            diagram_id=str(diagram.id),
            graph_name=diagram.graph_name
        )
        
        # Sync to FalkorDB
        if diagram_in.nodes is not None or diagram_in.edges is not None:
            try:
                nodes = [node.dict() for node in diagram_in.nodes] if diagram_in.nodes else []
                edges = [edge.dict() for edge in diagram_in.edges] if diagram_in.edges else []
                
                sync_result = await semantic_service.sync_to_falkordb(
                    graph_name=diagram.graph_name,
                    nodes=nodes,
                    edges=edges
                )
                logger.info("falkordb_sync_complete", result=sync_result)
            except Exception as sync_error:
                logger.warning("falkordb_sync_failed", error=str(sync_error))
        
        return DiagramResponse(
            id=diagram.id,
            name=diagram.name,
            description=diagram.description,
            workspace_name=diagram.workspace_name,
            graph_name=diagram.graph_name,
            notation=diagram.notation,
            is_published=diagram.is_published,
            published_at=diagram.published_at,
            settings=diagram.settings,
            created_at=diagram.created_at,
            updated_at=diagram.updated_at,
            created_by=str(diagram.created_by) if diagram.created_by else None,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("diagram_update_failed", error=str(e))
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update diagram: {str(e)}"
        )


@router.post("/{diagram_id}/sync")
async def sync_diagram_to_falkordb(
    *,
    db: AsyncSession = Depends(get_db),
    diagram_id: str,
    sync_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    semantic_service: SemanticModelService = Depends(get_semantic_service)
) -> Any:
    """
    Manually sync diagram to FalkorDB
    """
    try:
        # Get diagram
        stmt = select(Diagram).where(
            and_(
                Diagram.id == diagram_id,
                Diagram.deleted_at.is_(None)
            )
        )
        result = await db.execute(stmt)
        diagram = result.scalar_one_or_none()
        
        if not diagram:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Diagram not found"
            )
        
        nodes = sync_data.get("nodes", [])
        edges = sync_data.get("edges", [])
        
        logger.info(
            "manual_sync_request",
            diagram_id=str(diagram.id),
            graph_name=diagram.graph_name,
            node_count=len(nodes),
            edge_count=len(edges)
        )
        
        # Sync to FalkorDB
        sync_result = await semantic_service.sync_to_falkordb(
            graph_name=diagram.graph_name,
            nodes=nodes,
            edges=edges
        )
        
        return {
            "success": True,
            "diagram_id": str(diagram.id),
            "graph_name": diagram.graph_name,
            "sync_result": sync_result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("manual_sync_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync diagram: {str(e)}"
        )


@router.get("/{diagram_id}", response_model=DiagramResponse)
async def get_diagram(
    *,
    db: AsyncSession = Depends(get_db),
    diagram_id: str,
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get diagram by ID"""
    stmt = select(Diagram).where(
        and_(
            Diagram.id == diagram_id,
            Diagram.deleted_at.is_(None)
        )
    )
    result = await db.execute(stmt)
    diagram = result.scalar_one_or_none()
    
    if not diagram:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diagram not found"
        )
    
    return DiagramResponse(
        id=diagram.id,
        name=diagram.name,
        description=diagram.description,
        workspace_name=diagram.workspace_name,
        graph_name=diagram.graph_name,
        notation=diagram.notation,
        is_published=diagram.is_published,
        published_at=diagram.published_at,
        settings=diagram.settings,
        created_at=diagram.created_at,
        updated_at=diagram.updated_at,
        created_by=str(diagram.created_by) if diagram.created_by else None,
    )


@router.post("/{diagram_id}/publish")
async def publish_diagram(
    *,
    db: AsyncSession = Depends(get_db),
    diagram_id: str,
    current_user: User = Depends(get_current_user)
) -> Any:
    """Publish diagram to public library"""
    stmt = select(Diagram).where(
        and_(
            Diagram.id == diagram_id,
            Diagram.deleted_at.is_(None)
        )
    )
    result = await db.execute(stmt)
    diagram = result.scalar_one_or_none()
    
    if not diagram:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diagram not found"
        )
    
    diagram.is_published = True
    diagram.published_at = datetime.utcnow()
    diagram.updated_by = current_user.id
    
    await db.commit()
    
    logger.info(
        "diagram_published",
        diagram_id=str(diagram.id),
        name=diagram.name
    )
    
    return {"success": True, "message": "Diagram published successfully"}


@router.get("", response_model=List[DiagramResponse])
async def list_diagrams(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_name: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> Any:
    """List all diagrams for current user"""
    stmt = select(Diagram).where(
        and_(
            Diagram.created_by == current_user.id,
            Diagram.deleted_at.is_(None)
        )
    )
    
    if workspace_name:
        stmt = stmt.where(Diagram.workspace_name == workspace_name)
    
    stmt = stmt.order_by(Diagram.updated_at.desc()).offset(skip).limit(limit)
    
    result = await db.execute(stmt)
    diagrams = result.scalars().all()
    
    return [
        DiagramResponse(
            id=d.id,
            name=d.name,
            description=d.description,
            workspace_name=d.workspace_name,
            graph_name=d.graph_name,
            notation=d.notation,
            is_published=d.is_published,
            published_at=d.published_at,
            settings=d.settings,
            created_at=d.created_at,
            updated_at=d.updated_at,
            created_by=str(d.created_by) if d.created_by else None,
        )
        for d in diagrams
    ]