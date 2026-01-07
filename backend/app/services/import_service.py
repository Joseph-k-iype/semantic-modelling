# backend/app/services/import_service.py
"""
Import Service - Core logic for data import functionality
Handles file processing, mapping, transformation, and diagram creation
"""
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import structlog
import uuid
import json
import csv
import io
from pathlib import Path
from datetime import datetime
import tempfile

# File processing libraries
import pandas as pd
import openpyxl

from app.models.diagram import Diagram
from app.schemas.diagram import NodeBase, EdgeBase, DiagramCreate
from app.schemas.import_template import (
    ImportTemplate,
    NodeTemplate,
    EdgeTemplate,
    ImportMappingConfig,
    ImportPreviewResponse,
    ImportExecutionResponse,
    NodeType,
    EdgeType,
    NodeMappingConfig,
    EdgeMappingConfig,
)
from app.services.semantic_model_service import SemanticModelService

logger = structlog.get_logger()


class ImportService:
    """Service for handling data imports"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.semantic_service = SemanticModelService()
        self.temp_files: Dict[str, Dict[str, Any]] = {}  # In-memory storage for uploaded files
    
    async def process_uploaded_file(
        self,
        filename: str,
        content: bytes,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Process uploaded file and return preview data
        
        Args:
            filename: Original filename
            content: File content
            user_id: User ID
            
        Returns:
            File metadata and preview
        """
        file_ext = Path(filename).suffix.lower()
        file_id = str(uuid.uuid4())
        
        # Determine file type and parse
        if file_ext == '.csv':
            file_type = "csv"
            preview_data, detected_structure = self._process_csv(content)
        elif file_ext in ['.xlsx', '.xls']:
            file_type = "excel"
            preview_data, detected_structure = self._process_excel(content)
        elif file_ext == '.json':
            file_type = "json"
            preview_data, detected_structure = self._process_json(content)
        else:
            raise ValueError(f"Unsupported file type: {file_ext}")
        
        # Store temporarily
        self.temp_files[file_id] = {
            "filename": filename,
            "content": content,
            "file_type": file_type,
            "user_id": user_id,
            "uploaded_at": datetime.utcnow(),
            "parsed_data": preview_data
        }
        
        return {
            "file_id": file_id,
            "filename": filename,
            "file_type": file_type,
            "preview_data": preview_data,
            "detected_structure": detected_structure
        }
    
    def _process_csv(self, content: bytes) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Process CSV file"""
        # Parse CSV
        text_content = content.decode('utf-8')
        df = pd.read_csv(io.StringIO(text_content))
        
        # Preview data
        preview_data = {
            "columns": list(df.columns),
            "row_count": len(df),
            "sample_rows": df.head(5).to_dict('records')
        }
        
        # Auto-detect structure
        detected_structure = self._detect_csv_structure(df)
        
        return preview_data, detected_structure
    
    def _process_excel(self, content: bytes) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Process Excel file"""
        # Load workbook
        excel_file = io.BytesIO(content)
        workbook = pd.ExcelFile(excel_file)
        
        sheets_data = {}
        for sheet_name in workbook.sheet_names:
            df = pd.read_excel(excel_file, sheet_name=sheet_name)
            sheets_data[sheet_name] = {
                "columns": list(df.columns),
                "row_count": len(df),
                "sample_rows": df.head(5).to_dict('records')
            }
        
        preview_data = {
            "sheets": list(workbook.sheet_names),
            "sheets_data": sheets_data
        }
        
        # Auto-detect structure
        detected_structure = self._detect_excel_structure(sheets_data)
        
        return preview_data, detected_structure
    
    def _process_json(self, content: bytes) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Process JSON file"""
        json_data = json.loads(content.decode('utf-8'))
        
        preview_data = {
            "structure": self._get_json_structure(json_data),
            "sample": json_data if isinstance(json_data, dict) else json_data[:5]
        }
        
        # Auto-detect structure
        detected_structure = self._detect_json_structure(json_data)
        
        return preview_data, detected_structure
    
    def _detect_csv_structure(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Auto-detect CSV structure and suggest mappings"""
        columns = [col.lower() for col in df.columns]
        
        suggestions = {
            "has_id_column": any('id' in col for col in columns),
            "has_type_column": any('type' in col for col in columns),
            "has_label_column": any('label' in col or 'name' in col for col in columns),
            "has_attributes": any('attribute' in col for col in columns),
            "has_methods": any('method' in col for col in columns),
            "has_relationships": any(col in ['source', 'target', 'from', 'to'] for col in columns)
        }
        
        # Suggest node mappings
        node_mapping = {}
        if suggestions["has_id_column"]:
            node_mapping["id_column"] = next((col for col in df.columns if 'id' in col.lower()), None)
        if suggestions["has_label_column"]:
            node_mapping["label_column"] = next((col for col in df.columns if 'label' in col.lower() or 'name' in col.lower()), None)
        if suggestions["has_type_column"]:
            node_mapping["type_column"] = next((col for col in df.columns if 'type' in col.lower()), None)
        
        return {
            "suggestions": suggestions,
            "recommended_node_mapping": node_mapping,
            "format": "tabular"
        }
    
    def _detect_excel_structure(self, sheets_data: Dict[str, Any]) -> Dict[str, Any]:
        """Auto-detect Excel structure"""
        sheet_names = [name.lower() for name in sheets_data.keys()]
        
        suggestions = {
            "has_nodes_sheet": any('node' in name or 'class' in name or 'entity' in name for name in sheet_names),
            "has_edges_sheet": any('edge' in name or 'relation' in name or 'link' in name for name in sheet_names),
            "sheet_count": len(sheets_data)
        }
        
        # Suggest which sheets to use
        nodes_sheet = next((name for name in sheets_data.keys() if 'node' in name.lower() or 'class' in name.lower()), None)
        edges_sheet = next((name for name in sheets_data.keys() if 'edge' in name.lower() or 'relation' in name.lower()), None)
        
        return {
            "suggestions": suggestions,
            "recommended_nodes_sheet": nodes_sheet,
            "recommended_edges_sheet": edges_sheet,
            "format": "multi_sheet"
        }
    
    def _detect_json_structure(self, json_data: Any) -> Dict[str, Any]:
        """Auto-detect JSON structure"""
        if isinstance(json_data, dict):
            has_nodes = 'nodes' in json_data or 'classes' in json_data or 'entities' in json_data
            has_edges = 'edges' in json_data or 'relationships' in json_data or 'links' in json_data
            
            return {
                "suggestions": {
                    "matches_template": has_nodes and has_edges,
                    "has_nodes_key": has_nodes,
                    "has_edges_key": has_edges
                },
                "format": "template_format" if has_nodes else "custom_format"
            }
        
        return {
            "suggestions": {
                "is_array": isinstance(json_data, list),
                "array_length": len(json_data) if isinstance(json_data, list) else 0
            },
            "format": "array_format"
        }
    
    def _get_json_structure(self, data: Any, max_depth: int = 3) -> Dict[str, Any]:
        """Get JSON structure recursively"""
        if max_depth == 0:
            return {"type": "...", "truncated": True}
        
        if isinstance(data, dict):
            return {
                "type": "object",
                "keys": {
                    k: self._get_json_structure(v, max_depth - 1)
                    for k, v in list(data.items())[:10]  # Limit to 10 keys
                }
            }
        elif isinstance(data, list):
            return {
                "type": "array",
                "length": len(data),
                "item_structure": self._get_json_structure(data[0], max_depth - 1) if data else {}
            }
        else:
            return {"type": type(data).__name__}
    
    async def preview_import(
        self,
        mapping_config: ImportMappingConfig,
        user_id: str
    ) -> ImportPreviewResponse:
        """
        Generate preview of import based on mapping configuration
        
        Args:
            mapping_config: Mapping configuration
            user_id: User ID
            
        Returns:
            Preview response
        """
        # Get uploaded file
        temp_file = self.temp_files.get(mapping_config.file_id)
        if not temp_file or temp_file["user_id"] != user_id:
            raise ValueError("File not found or access denied")
        
        # Transform data based on mappings
        import_template = await self._transform_data(temp_file, mapping_config)
        
        # Count by type
        node_type_counts = {}
        for node in import_template.nodes:
            node_type_counts[node.type] = node_type_counts.get(node.type, 0) + 1
        
        edge_type_counts = {}
        for edge in import_template.edges:
            edge_type_counts[edge.type] = edge_type_counts.get(edge.type, 0) + 1
        
        # Validation warnings/errors
        warnings = []
        errors = []
        
        # Check for orphaned edges
        node_ids = {node.id for node in import_template.nodes}
        for edge in import_template.edges:
            if edge.source not in node_ids:
                errors.append(f"Edge source '{edge.source}' not found in nodes")
            if edge.target not in node_ids:
                errors.append(f"Edge target '{edge.target}' not found in nodes")
        
        # Check for duplicate IDs
        if len(node_ids) != len(import_template.nodes):
            warnings.append("Duplicate node IDs detected - will be auto-resolved")
        
        return ImportPreviewResponse(
            total_nodes=len(import_template.nodes),
            total_edges=len(import_template.edges),
            node_type_counts=node_type_counts,
            edge_type_counts=edge_type_counts,
            preview_nodes=import_template.nodes[:10],  # First 10 nodes
            preview_edges=import_template.edges[:10],  # First 10 edges
            warnings=warnings,
            errors=errors
        )
    
    async def execute_import(
        self,
        mapping_config: ImportMappingConfig,
        user_id: str,
        username: str
    ) -> ImportExecutionResponse:
        """
        Execute the import and create diagram
        
        Args:
            mapping_config: Mapping configuration
            user_id: User ID
            username: Username for graph naming
            
        Returns:
            Execution response
        """
        # Get uploaded file
        temp_file = self.temp_files.get(mapping_config.file_id)
        if not temp_file or temp_file["user_id"] != user_id:
            raise ValueError("File not found or access denied")
        
        try:
            # Transform data
            import_template = await self._transform_data(temp_file, mapping_config)
            
            # Apply auto-layout if requested
            if mapping_config.auto_layout:
                import_template = self._apply_auto_layout(
                    import_template,
                    mapping_config.layout_algorithm
                )
            
            # Create diagram
            result = await self.direct_import(
                template_data=import_template,
                diagram_name=mapping_config.diagram_name,
                workspace_name=mapping_config.workspace_name,
                user_id=user_id,
                username=username
            )
            
            # Cleanup temp file
            await self.delete_temp_file(mapping_config.file_id, user_id)
            
            return result
            
        except Exception as e:
            logger.error("import_execution_failed", error=str(e))
            raise
    
    async def direct_import(
        self,
        template_data: ImportTemplate,
        diagram_name: str,
        workspace_name: str,
        user_id: str,
        username: str
    ) -> ImportExecutionResponse:
        """
        Direct import from template data
        
        Args:
            template_data: Import template
            diagram_name: Diagram name
            workspace_name: Workspace name
            user_id: User ID
            username: Username
            
        Returns:
            Execution response
        """
        warnings = []
        errors = []
        
        try:
            # Convert template to diagram nodes/edges
            nodes = self._convert_template_nodes(template_data.nodes)
            edges = self._convert_template_edges(template_data.edges)
            
            # Generate graph name
            graph_name = f"{username}/{workspace_name}/{diagram_name}"
            
            # Check for existing diagram
            stmt = select(Diagram).where(
                and_(
                    Diagram.graph_name == graph_name,
                    Diagram.deleted_at.is_(None)
                )
            )
            result = await self.db.execute(stmt)
            existing = result.scalar_one_or_none()
            
            if existing:
                # Add suffix to make unique
                suffix = str(uuid.uuid4())[:8]
                diagram_name = f"{diagram_name}_{suffix}"
                graph_name = f"{username}/{workspace_name}/{diagram_name}"
                warnings.append(f"Diagram name already exists, renamed to: {diagram_name}")
            
            # Create diagram
            diagram = Diagram(
                name=diagram_name,
                description=f"Imported from file",
                workspace_name=workspace_name,
                notation="UML_CLASS",
                graph_name=graph_name,
                settings={
                    "nodes": [node.dict() for node in nodes],
                    "edges": [edge.dict() for edge in edges],
                    "viewport": {"x": 0, "y": 0, "zoom": 1}
                },
                is_published=False,
                created_by=uuid.UUID(user_id),
                updated_by=uuid.UUID(user_id)
            )
            
            self.db.add(diagram)
            await self.db.commit()
            await self.db.refresh(diagram)
            
            # Sync to FalkorDB
            try:
                sync_result = await self.semantic_service.sync_to_falkordb(
                    graph_name=graph_name,
                    nodes=[node.dict() for node in nodes],
                    edges=[edge.dict() for edge in edges]
                )
                logger.info("falkordb_sync_complete", result=sync_result)
            except Exception as sync_error:
                logger.warning("falkordb_sync_failed", error=str(sync_error))
                warnings.append(f"FalkorDB sync warning: {str(sync_error)}")
            
            return ImportExecutionResponse(
                success=True,
                diagram_id=str(diagram.id),
                nodes_imported=len(nodes),
                edges_imported=len(edges),
                warnings=warnings,
                errors=errors
            )
            
        except Exception as e:
            await self.db.rollback()
            logger.error("direct_import_failed", error=str(e))
            raise
    
    async def _transform_data(
        self,
        temp_file: Dict[str, Any],
        mapping_config: ImportMappingConfig
    ) -> ImportTemplate:
        """Transform uploaded data based on mapping configuration"""
        file_type = temp_file["file_type"]
        parsed_data = temp_file["parsed_data"]
        
        if file_type == "csv":
            return await self._transform_csv_data(parsed_data, mapping_config)
        elif file_type == "excel":
            return await self._transform_excel_data(parsed_data, mapping_config)
        elif file_type == "json":
            return await self._transform_json_data(parsed_data, mapping_config)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
    
    async def _transform_csv_data(
        self,
        parsed_data: Dict[str, Any],
        mapping_config: ImportMappingConfig
    ) -> ImportTemplate:
        """Transform CSV data to import template"""
        # Reconstruct DataFrame
        df = pd.DataFrame(parsed_data["sample_rows"])
        
        nodes = []
        for node_mapping in mapping_config.node_mappings:
            for _, row in df.iterrows():
                # Apply filter if specified
                if node_mapping.filter_expression:
                    # Simple eval-based filter (in production, use safer method)
                    if not self._evaluate_filter(row, node_mapping.filter_expression):
                        continue
                
                # Extract node data
                node_id = str(row.get(node_mapping.id_column, str(uuid.uuid4()))) if node_mapping.id_column else str(uuid.uuid4())
                label = str(row[node_mapping.label_column])
                
                # Parse attributes
                attributes = []
                if node_mapping.attribute_columns:
                    for col in node_mapping.attribute_columns:
                        if col in row and pd.notna(row[col]):
                            # Parse semicolon-separated attributes
                            attr_str = str(row[col])
                            for attr in attr_str.split(';'):
                                if ':' in attr:
                                    name, type_str = attr.split(':', 1)
                                    attributes.append({
                                        "name": name.strip(),
                                        "type": type_str.strip(),
                                        "visibility": "+"
                                    })
                
                # Parse methods
                methods = []
                if node_mapping.method_columns:
                    for col in node_mapping.method_columns:
                        if col in row and pd.notna(row[col]):
                            # Parse semicolon-separated methods
                            method_str = str(row[col])
                            for method in method_str.split(';'):
                                methods.append(self._parse_method_string(method))
                
                node = NodeTemplate(
                    id=node_id,
                    type=node_mapping.node_type,
                    label=label,
                    attributes=attributes if attributes else None,
                    methods=methods if methods else None
                )
                nodes.append(node)
        
        # Transform edges if mapping exists
        edges = []
        for edge_mapping in mapping_config.edge_mappings:
            for _, row in df.iterrows():
                if edge_mapping.source_column in row and edge_mapping.target_column in row:
                    edge = EdgeTemplate(
                        source=str(row[edge_mapping.source_column]),
                        target=str(row[edge_mapping.target_column]),
                        type=edge_mapping.edge_type,
                        label=str(row[edge_mapping.label_column]) if edge_mapping.label_column else None
                    )
                    edges.append(edge)
        
        return ImportTemplate(nodes=nodes, edges=edges)
    
    async def _transform_excel_data(
        self,
        parsed_data: Dict[str, Any],
        mapping_config: ImportMappingConfig
    ) -> ImportTemplate:
        """Transform Excel data to import template"""
        # Similar to CSV transformation but handle multiple sheets
        # Implementation details...
        pass
    
    async def _transform_json_data(
        self,
        parsed_data: Dict[str, Any],
        mapping_config: ImportMappingConfig
    ) -> ImportTemplate:
        """Transform JSON data to import template"""
        # If JSON already matches template format, use directly
        # Otherwise, apply transformations
        pass
    
    def _evaluate_filter(self, row: pd.Series, expression: str) -> bool:
        """Safely evaluate filter expression"""
        # In production, implement safe expression evaluation
        # For now, simple implementation
        try:
            return eval(expression, {"row": row, "__builtins__": {}})
        except:
            return True
    
    def _parse_method_string(self, method_str: str) -> Dict[str, Any]:
        """Parse method string like 'login(password:String):boolean'"""
        # Extract method name, parameters, and return type
        import re
        match = re.match(r'(\w+)\((.*?)\):(\w+)', method_str.strip())
        if match:
            name, params, return_type = match.groups()
            param_list = [p.strip() for p in params.split(',') if p.strip()]
            return {
                "name": name,
                "return_type": return_type,
                "parameters": param_list,
                "visibility": "+"
            }
        return {"name": method_str, "return_type": "void", "parameters": [], "visibility": "+"}
    
    def _apply_auto_layout(
        self,
        template: ImportTemplate,
        algorithm: str
    ) -> ImportTemplate:
        """Apply automatic layout to nodes"""
        if algorithm == "hierarchical":
            # Implement hierarchical layout
            self._apply_hierarchical_layout(template)
        elif algorithm == "force":
            # Implement force-directed layout
            self._apply_force_layout(template)
        elif algorithm == "circular":
            # Implement circular layout
            self._apply_circular_layout(template)
        elif algorithm == "grid":
            # Implement grid layout
            self._apply_grid_layout(template)
        
        return template
    
    def _apply_hierarchical_layout(self, template: ImportTemplate):
        """Apply hierarchical layout"""
        # Simple implementation: arrange in rows based on depth
        x, y = 50, 50
        row_height = 150
        col_width = 300
        
        for i, node in enumerate(template.nodes):
            node.x = x + (i % 4) * col_width
            node.y = y + (i // 4) * row_height
    
    def _apply_force_layout(self, template: ImportTemplate):
        """Apply force-directed layout (simplified)"""
        # Placeholder - in production, use proper force-directed algorithm
        self._apply_grid_layout(template)
    
    def _apply_circular_layout(self, template: ImportTemplate):
        """Apply circular layout"""
        import math
        center_x, center_y = 500, 400
        radius = 300
        n = len(template.nodes)
        
        for i, node in enumerate(template.nodes):
            angle = 2 * math.pi * i / n
            node.x = center_x + radius * math.cos(angle)
            node.y = center_y + radius * math.sin(angle)
    
    def _apply_grid_layout(self, template: ImportTemplate):
        """Apply grid layout"""
        x, y = 50, 50
        col_width = 300
        row_height = 150
        cols = 4
        
        for i, node in enumerate(template.nodes):
            node.x = x + (i % cols) * col_width
            node.y = y + (i // cols) * row_height
    
    def _convert_template_nodes(self, template_nodes: List[NodeTemplate]) -> List[NodeBase]:
        """Convert template nodes to diagram nodes"""
        nodes = []
        for template_node in template_nodes:
            # Build node data dictionary
            node_data = {
                "id": template_node.id,
                "type": template_node.type.value,
                "data": {
                    "label": template_node.label,
                    "type": template_node.type.value,
                }
            }
            
            # Add type-specific data
            if template_node.attributes:
                node_data["data"]["attributes"] = [attr.dict() for attr in template_node.attributes]
            if template_node.methods:
                node_data["data"]["methods"] = [method.dict() for method in template_node.methods]
            if template_node.literals:
                node_data["data"]["literals"] = [lit.dict() for lit in template_node.literals]
            if template_node.stereotype:
                node_data["data"]["stereotype"] = template_node.stereotype
            if template_node.is_abstract:
                node_data["data"]["isAbstract"] = template_node.is_abstract
            if template_node.parent_package_id:
                node_data["data"]["parentPackageId"] = template_node.parent_package_id
            
            # Position
            node_data["position"] = {
                "x": template_node.x or 0,
                "y": template_node.y or 0
            }
            
            nodes.append(NodeBase(**node_data))
        
        return nodes
    
    def _convert_template_edges(self, template_edges: List[EdgeTemplate]) -> List[EdgeBase]:
        """Convert template edges to diagram edges"""
        edges = []
        for template_edge in template_edges:
            edge_data = {
                "id": f"edge_{uuid.uuid4()}",
                "source": template_edge.source,
                "target": template_edge.target,
                "type": "custom",
                "data": {
                    "relationshipType": template_edge.type.value,
                    "label": template_edge.label,
                    "sourceMultiplicity": template_edge.source_multiplicity,
                    "targetMultiplicity": template_edge.target_multiplicity,
                }
            }
            
            edges.append(EdgeBase(**edge_data))
        
        return edges
    
    async def delete_temp_file(self, file_id: str, user_id: str):
        """Delete temporary file"""
        temp_file = self.temp_files.get(file_id)
        if temp_file and temp_file["user_id"] == user_id:
            del self.temp_files[file_id]