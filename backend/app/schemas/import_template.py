# backend/app/schemas/import_template.py
"""
Data Import Template Schema
Defines the expected structure for importing UML elements
"""
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field
from enum import Enum


class NodeType(str, Enum):
    """UML Node Types"""
    PACKAGE = "package"
    CLASS = "class"
    OBJECT = "object"
    INTERFACE = "interface"
    ENUMERATION = "enumeration"


class EdgeType(str, Enum):
    """UML Relationship Types"""
    ASSOCIATION = "association"
    AGGREGATION = "aggregation"
    COMPOSITION = "composition"
    GENERALIZATION = "generalization"
    REALIZATION = "realization"
    DEPENDENCY = "dependency"


class AttributeTemplate(BaseModel):
    """Template for class/interface attributes"""
    name: str = Field(..., description="Attribute name")
    type: str = Field(default="String", description="Data type")
    visibility: Literal["+", "-", "#", "~"] = Field(default="+", description="Visibility: +public, -private, #protected, ~package")
    is_static: bool = Field(default=False, description="Is static attribute")
    default_value: Optional[str] = Field(None, description="Default value")


class MethodTemplate(BaseModel):
    """Template for class/interface methods"""
    name: str = Field(..., description="Method name")
    return_type: str = Field(default="void", description="Return type")
    parameters: List[str] = Field(default_factory=list, description="Parameter list (format: 'name: type')")
    visibility: Literal["+", "-", "#", "~"] = Field(default="+", description="Visibility")
    is_static: bool = Field(default=False, description="Is static method")
    is_abstract: bool = Field(default=False, description="Is abstract method")


class LiteralTemplate(BaseModel):
    """Template for enumeration literals"""
    name: str = Field(..., description="Literal name")
    value: Optional[str] = Field(None, description="Literal value")


class NodeTemplate(BaseModel):
    """Template for UML nodes"""
    id: str = Field(..., description="Unique identifier (will be generated if not provided)")
    type: NodeType = Field(..., description="Node type")
    label: str = Field(..., description="Node display name")
    
    # Type-specific fields
    attributes: Optional[List[AttributeTemplate]] = Field(None, description="For CLASS/INTERFACE")
    methods: Optional[List[MethodTemplate]] = Field(None, description="For CLASS/INTERFACE")
    literals: Optional[List[LiteralTemplate]] = Field(None, description="For ENUMERATION")
    parent_package_id: Optional[str] = Field(None, description="Parent package ID for nesting")
    
    # Optional metadata
    stereotype: Optional[str] = Field(None, description="UML stereotype")
    is_abstract: bool = Field(default=False, description="Is abstract class")
    description: Optional[str] = Field(None, description="Node description")
    
    # Position (optional - will be auto-arranged if not provided)
    x: Optional[float] = Field(None, description="X coordinate")
    y: Optional[float] = Field(None, description="Y coordinate")


class EdgeTemplate(BaseModel):
    """Template for UML relationships"""
    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    type: EdgeType = Field(..., description="Relationship type")
    label: Optional[str] = Field(None, description="Edge label")
    
    # Multiplicity
    source_multiplicity: Optional[str] = Field(None, description="Source multiplicity (e.g., '1', '0..*', '1..*')")
    target_multiplicity: Optional[str] = Field(None, description="Target multiplicity")
    
    # Optional properties
    is_navigable: bool = Field(default=True, description="Is navigable relationship")
    description: Optional[str] = Field(None, description="Relationship description")


class ImportTemplate(BaseModel):
    """Complete import template structure"""
    nodes: List[NodeTemplate] = Field(..., description="List of UML nodes to import")
    edges: List[EdgeTemplate] = Field(default_factory=list, description="List of UML relationships to import")
    
    class Config:
        json_schema_extra = {
            "example": {
                "nodes": [
                    {
                        "id": "class_1",
                        "type": "class",
                        "label": "User",
                        "attributes": [
                            {"name": "id", "type": "UUID", "visibility": "-"},
                            {"name": "username", "type": "String", "visibility": "+"}
                        ],
                        "methods": [
                            {"name": "login", "return_type": "boolean", "parameters": ["password: String"]}
                        ]
                    },
                    {
                        "id": "class_2",
                        "type": "class",
                        "label": "Account",
                        "attributes": [
                            {"name": "balance", "type": "Decimal", "visibility": "-"}
                        ]
                    }
                ],
                "edges": [
                    {
                        "source": "class_1",
                        "target": "class_2",
                        "type": "association",
                        "label": "owns",
                        "source_multiplicity": "1",
                        "target_multiplicity": "1..*"
                    }
                ]
            }
        }


# ============================================================================
# FILE UPLOAD & MAPPING SCHEMAS
# ============================================================================

class FileUploadResponse(BaseModel):
    """Response after file upload"""
    file_id: str = Field(..., description="Temporary file identifier")
    filename: str = Field(..., description="Original filename")
    file_type: Literal["csv", "excel", "json"] = Field(..., description="Detected file type")
    preview_data: Dict[str, Any] = Field(..., description="Preview of file structure")
    detected_structure: Dict[str, Any] = Field(..., description="Auto-detected structure hints")


class ColumnMapping(BaseModel):
    """Mapping from source column to template field"""
    source_column: str = Field(..., description="Column name in source data")
    target_field: str = Field(..., description="Field in template (e.g., 'label', 'attributes.name')")
    transformation: Optional[str] = Field(None, description="Optional transformation function")


class NodeMappingConfig(BaseModel):
    """Configuration for mapping source data to nodes"""
    node_type: NodeType = Field(..., description="Target node type")
    id_column: Optional[str] = Field(None, description="Column to use as node ID")
    label_column: str = Field(..., description="Column to use as node label")
    
    # Attribute mappings (for classes/interfaces)
    attribute_columns: Optional[List[str]] = Field(None, description="Columns to map as attributes")
    method_columns: Optional[List[str]] = Field(None, description="Columns to map as methods")
    
    # Enumeration mappings
    literal_columns: Optional[List[str]] = Field(None, description="Columns to map as enum literals")
    
    # Additional mappings
    column_mappings: List[ColumnMapping] = Field(default_factory=list, description="Custom column mappings")
    
    # Filters
    filter_expression: Optional[str] = Field(None, description="Optional filter (e.g., 'type == \"customer\"')")


class EdgeMappingConfig(BaseModel):
    """Configuration for mapping source data to edges"""
    edge_type: EdgeType = Field(..., description="Relationship type")
    source_column: str = Field(..., description="Column containing source node identifier")
    target_column: str = Field(..., description="Column containing target node identifier")
    label_column: Optional[str] = Field(None, description="Column for edge label")
    
    # Multiplicity mappings
    source_multiplicity_column: Optional[str] = Field(None, description="Source multiplicity column")
    target_multiplicity_column: Optional[str] = Field(None, description="Target multiplicity column")


class ImportMappingConfig(BaseModel):
    """Complete mapping configuration"""
    file_id: str = Field(..., description="File identifier from upload")
    diagram_name: str = Field(..., description="Target diagram name")
    workspace_name: str = Field(..., description="Target workspace name")
    
    # Data source configuration
    sheet_name: Optional[str] = Field(None, description="Excel sheet name (if applicable)")
    data_path: Optional[str] = Field(None, description="JSON path to data (if applicable)")
    
    # Mapping configurations
    node_mappings: List[NodeMappingConfig] = Field(..., description="Node mapping configurations")
    edge_mappings: List[EdgeMappingConfig] = Field(default_factory=list, description="Edge mapping configurations")
    
    # Layout options
    auto_layout: bool = Field(default=True, description="Automatically arrange nodes")
    layout_algorithm: Literal["hierarchical", "force", "circular", "grid"] = Field(
        default="hierarchical",
        description="Layout algorithm to use"
    )


class ImportPreviewResponse(BaseModel):
    """Preview of import before execution"""
    total_nodes: int
    total_edges: int
    node_type_counts: Dict[NodeType, int]
    edge_type_counts: Dict[EdgeType, int]
    preview_nodes: List[NodeTemplate]
    preview_edges: List[EdgeTemplate]
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)


class ImportExecutionResponse(BaseModel):
    """Response after import execution"""
    success: bool
    diagram_id: str
    nodes_imported: int
    edges_imported: int
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)