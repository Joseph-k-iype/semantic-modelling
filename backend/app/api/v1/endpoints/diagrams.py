"""
Diagram API endpoints
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.db.session import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.diagram import Diagram
from app.services.diagram_service import DiagramService
from app.services.semantic_model_service import SemanticModelService
from app.schemas.diagram import (
    DiagramCreate,
    DiagramUpdate,
    DiagramResponse,
    DiagramDetailResponse,
)

router = APIRouter()


@router.get("/", response_model=List[DiagramResponse])
async def list_diagrams(
    model_id: Optional[str] = None,
    workspace_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all diagrams for a model or workspace
    """
    diagram_service = DiagramService(db)
    
    if model_id:
        diagrams = diagram_service.get_diagrams_by_model(
            model_id=model_id,
            skip=skip,
            limit=limit
        )
    elif workspace_id:
        diagrams = diagram_service.get_diagrams_by_workspace(
            workspace_id=workspace_id,
            skip=skip,
            limit=limit
        )
    else:
        diagrams = diagram_service.get_user_diagrams(
            user_id=current_user.id,
            skip=skip,
            limit=limit
        )
    
    return diagrams


@router.post("/", response_model=DiagramDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_diagram(
    diagram_data: DiagramCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new diagram
    """
    diagram_service = DiagramService(db)
    semantic_service = SemanticModelService(db)
    
    # Create diagram in PostgreSQL
    diagram = diagram_service.create_diagram(
        data=diagram_data,
        user_id=current_user.id
    )
    
    # Sync to graph database (semantic model)
    try:
        semantic_service.sync_diagram_to_graph(diagram)
    except Exception as e:
        # Log error but don't fail the request
        print(f"Error syncing to graph: {str(e)}")
    
    return diagram


@router.get("/{diagram_id}", response_model=DiagramDetailResponse)
async def get_diagram(
    diagram_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get a specific diagram by ID
    """
    diagram_service = DiagramService(db)
    
    diagram = diagram_service.get_diagram(diagram_id)
    if not diagram:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diagram not found"
        )
    
    # Check access permissions
    # TODO: Implement proper permission checking
    
    return diagram


@router.put("/{diagram_id}", response_model=DiagramDetailResponse)
async def update_diagram(
    diagram_id: str,
    diagram_data: DiagramUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update a diagram
    """
    diagram_service = DiagramService(db)
    semantic_service = SemanticModelService(db)
    
    diagram = diagram_service.get_diagram(diagram_id)
    if not diagram:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diagram not found"
        )
    
    # Update diagram
    updated_diagram = diagram_service.update_diagram(
        diagram_id=diagram_id,
        data=diagram_data,
        user_id=current_user.id
    )
    
    # Sync to graph database
    try:
        semantic_service.sync_diagram_to_graph(updated_diagram)
    except Exception as e:
        print(f"Error syncing to graph: {str(e)}")
    
    return updated_diagram


@router.delete("/{diagram_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_diagram(
    diagram_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a diagram
    """
    diagram_service = DiagramService(db)
    semantic_service = SemanticModelService(db)
    
    diagram = diagram_service.get_diagram(diagram_id)
    if not diagram:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diagram not found"
        )
    
    # Delete from graph database first
    try:
        semantic_service.delete_diagram_from_graph(diagram_id)
    except Exception as e:
        print(f"Error deleting from graph: {str(e)}")
    
    # Delete from PostgreSQL
    diagram_service.delete_diagram(diagram_id)
    
    return None


@router.post("/{diagram_id}/convert-to-sql")
async def convert_diagram_to_sql(
    diagram_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Convert ER diagram to SQL DDL statements
    """
    diagram_service = DiagramService(db)
    
    diagram = diagram_service.get_diagram(diagram_id)
    if not diagram:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diagram not found"
        )
    
    if diagram.type != "ER":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only ER diagrams can be converted to SQL"
        )
    
    sql_statements = diagram_service.convert_to_sql(diagram)
    
    return {
        "diagram_id": diagram_id,
        "diagram_name": diagram.name,
        "sql": sql_statements
    }


@router.post("/{diagram_id}/convert-to-cypher")
async def convert_diagram_to_cypher(
    diagram_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Convert diagram to Cypher (graph query language)
    """
    diagram_service = DiagramService(db)
    
    diagram = diagram_service.get_diagram(diagram_id)
    if not diagram:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diagram not found"
        )
    
    cypher_statements = diagram_service.convert_to_cypher(diagram)
    
    return {
        "diagram_id": diagram_id,
        "diagram_name": diagram.name,
        "cypher": cypher_statements
    }


@router.post("/{diagram_id}/validate")
async def validate_diagram(
    diagram_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Validate diagram according to notation rules
    """
    diagram_service = DiagramService(db)
    
    diagram = diagram_service.get_diagram(diagram_id)
    if not diagram:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diagram not found"
        )
    
    validation_results = diagram_service.validate_diagram(diagram)
    
    return {
        "diagram_id": diagram_id,
        "is_valid": validation_results["is_valid"],
        "errors": validation_results.get("errors", []),
        "warnings": validation_results.get("warnings", [])
    }


@router.post("/{diagram_id}/auto-layout")
async def auto_layout_diagram(
    diagram_id: str,
    algorithm: str = "layered",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Apply automatic layout to diagram
    """
    diagram_service = DiagramService(db)
    
    diagram = diagram_service.get_diagram(diagram_id)
    if not diagram:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diagram not found"
        )
    
    laid_out_diagram = diagram_service.apply_auto_layout(
        diagram=diagram,
        algorithm=algorithm
    )
    
    return laid_out_diagram


@router.get("/{diagram_id}/export/{format}")
async def export_diagram(
    diagram_id: str,
    format: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Export diagram to various formats (SVG, PNG, PDF, etc.)
    """
    diagram_service = DiagramService(db)
    
    diagram = diagram_service.get_diagram(diagram_id)
    if not diagram:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diagram not found"
        )
    
    if format not in ["svg", "png", "pdf", "json", "xmi"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported export format: {format}"
        )
    
    exported_data = diagram_service.export_diagram(
        diagram=diagram,
        format=format
    )
    
    return {
        "diagram_id": diagram_id,
        "format": format,
        "data": exported_data
    }