"""
Diagram Service - Handles diagram business logic
"""
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.diagram import Diagram
from app.models.layout import Layout
from app.schemas.diagram import DiagramCreate, DiagramUpdate
from app.validation.validation_engine import ValidationEngine
from app.exporters.sql_exporter import SQLExporter
from app.exporters.cypher_exporter import CypherExporter
from app.layout.layout_engine import LayoutEngine
from app.utils.logger import get_logger

logger = get_logger(__name__)


class DiagramService:
    """Service for managing diagrams"""
    
    def __init__(self, db: Session):
        self.db = db
        self.validation_engine = ValidationEngine()
        self.sql_exporter = SQLExporter()
        self.cypher_exporter = CypherExporter()
        self.layout_engine = LayoutEngine()
    
    def get_diagram(self, diagram_id: str) -> Optional[Diagram]:
        """Get a diagram by ID"""
        return self.db.query(Diagram).filter(Diagram.id == diagram_id).first()
    
    def get_diagrams_by_model(
        self,
        model_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Diagram]:
        """Get all diagrams for a model"""
        return (
            self.db.query(Diagram)
            .filter(Diagram.model_id == model_id)
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_diagrams_by_workspace(
        self,
        workspace_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Diagram]:
        """Get all diagrams for a workspace"""
        return (
            self.db.query(Diagram)
            .filter(Diagram.workspace_id == workspace_id)
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_user_diagrams(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Diagram]:
        """Get all diagrams created by a user"""
        return (
            self.db.query(Diagram)
            .filter(Diagram.created_by == user_id)
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def create_diagram(
        self,
        data: DiagramCreate,
        user_id: str
    ) -> Diagram:
        """Create a new diagram"""
        diagram = Diagram(
            name=data.name,
            type=data.type,
            model_id=data.model_id,
            workspace_id=data.workspace_id,
            nodes=data.nodes or [],
            edges=data.edges or [],
            viewport=data.viewport or {"x": 0, "y": 0, "zoom": 1},
            created_by=user_id,
            updated_by=user_id,
        )
        
        self.db.add(diagram)
        self.db.commit()
        self.db.refresh(diagram)
        
        logger.info(f"Created diagram {diagram.id} by user {user_id}")
        
        return diagram
    
    def update_diagram(
        self,
        diagram_id: str,
        data: DiagramUpdate,
        user_id: str
    ) -> Diagram:
        """Update an existing diagram"""
        diagram = self.get_diagram(diagram_id)
        
        if data.name is not None:
            diagram.name = data.name
        
        if data.type is not None:
            diagram.type = data.type
        
        if data.nodes is not None:
            diagram.nodes = data.nodes
        
        if data.edges is not None:
            diagram.edges = data.edges
        
        if data.viewport is not None:
            diagram.viewport = data.viewport
        
        diagram.updated_by = user_id
        diagram.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(diagram)
        
        logger.info(f"Updated diagram {diagram_id} by user {user_id}")
        
        return diagram
    
    def delete_diagram(self, diagram_id: str) -> None:
        """Delete a diagram"""
        diagram = self.get_diagram(diagram_id)
        self.db.delete(diagram)
        self.db.commit()
        
        logger.info(f"Deleted diagram {diagram_id}")
    
    def convert_to_sql(self, diagram: Diagram) -> str:
        """
        Convert ER diagram to SQL DDL statements
        """
        if diagram.type != "ER":
            raise ValueError("Only ER diagrams can be converted to SQL")
        
        nodes = diagram.nodes
        edges = diagram.edges
        
        sql_statements = self.sql_exporter.export(nodes, edges)
        
        logger.info(f"Converted diagram {diagram.id} to SQL")
        
        return sql_statements
    
    def convert_to_cypher(self, diagram: Diagram) -> str:
        """
        Convert diagram to Cypher statements
        """
        nodes = diagram.nodes
        edges = diagram.edges
        
        cypher_statements = self.cypher_exporter.export(nodes, edges, diagram.type)
        
        logger.info(f"Converted diagram {diagram.id} to Cypher")
        
        return cypher_statements
    
    def validate_diagram(self, diagram: Diagram) -> Dict[str, Any]:
        """
        Validate diagram according to notation rules
        """
        nodes = diagram.nodes
        edges = diagram.edges
        diagram_type = diagram.type
        
        validation_results = self.validation_engine.validate(
            nodes=nodes,
            edges=edges,
            diagram_type=diagram_type
        )
        
        logger.info(
            f"Validated diagram {diagram.id}: "
            f"{len(validation_results.get('errors', []))} errors, "
            f"{len(validation_results.get('warnings', []))} warnings"
        )
        
        return validation_results
    
    def apply_auto_layout(
        self,
        diagram: Diagram,
        algorithm: str = "layered"
    ) -> Diagram:
        """
        Apply automatic layout algorithm to diagram
        """
        nodes = diagram.nodes
        edges = diagram.edges
        
        # Apply layout algorithm
        laid_out_nodes = self.layout_engine.apply_layout(
            nodes=nodes,
            edges=edges,
            algorithm=algorithm,
            diagram_type=diagram.type
        )
        
        # Update diagram nodes with new positions
        diagram.nodes = laid_out_nodes
        diagram.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(diagram)
        
        logger.info(f"Applied {algorithm} layout to diagram {diagram.id}")
        
        return diagram
    
    def export_diagram(
        self,
        diagram: Diagram,
        format: str
    ) -> str:
        """
        Export diagram to various formats
        """
        if format == "json":
            return json.dumps({
                "id": diagram.id,
                "name": diagram.name,
                "type": diagram.type,
                "nodes": diagram.nodes,
                "edges": diagram.edges,
                "viewport": diagram.viewport,
            }, indent=2)
        
        elif format == "svg":
            # TODO: Implement SVG export
            return "<svg>SVG export not yet implemented</svg>"
        
        elif format == "png":
            # TODO: Implement PNG export
            return "PNG export not yet implemented"
        
        elif format == "pdf":
            # TODO: Implement PDF export
            return "PDF export not yet implemented"
        
        elif format == "xmi":
            # TODO: Implement XMI export for UML
            return "XMI export not yet implemented"
        
        else:
            raise ValueError(f"Unsupported export format: {format}")