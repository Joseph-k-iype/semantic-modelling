"""
Export Pydantic schemas
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, UUID4, ConfigDict
from enum import Enum


class ExportFormat(str, Enum):
    """Export format enumeration"""
    SVG = "svg"
    PNG = "png"
    PDF = "pdf"
    SQL = "sql"
    CYPHER = "cypher"
    XMI = "xmi"
    JSON = "json"


class ExportRequest(BaseModel):
    """Schema for export request"""
    diagram_id: Optional[UUID4] = None
    model_id: Optional[UUID4] = None
    format: ExportFormat
    options: Dict[str, Any] = {}


class ExportOptions(BaseModel):
    """Export options schema"""
    include_metadata: bool = True
    include_version_info: bool = False
    include_lineage: bool = False
    paper_size: Optional[str] = None  # For PDF: A4, Letter, etc.
    orientation: Optional[str] = None  # For PDF: portrait, landscape
    resolution: Optional[int] = None  # For PNG: DPI
    sql_dialect: Optional[str] = None  # For SQL: postgresql, mysql, etc.
    
    model_config = ConfigDict(from_attributes=True)


class ExportResponse(BaseModel):
    """Export response schema"""
    format: ExportFormat
    file_name: str
    file_size: Optional[int] = None
    download_url: Optional[str] = None
    content: Optional[str] = None  # For text-based formats
    
    model_config = ConfigDict(from_attributes=True)


class ExportPreview(BaseModel):
    """Export preview schema"""
    format: ExportFormat
    preview_url: Optional[str] = None
    estimated_size: Optional[int] = None
    warnings: list[str] = []
    
    model_config = ConfigDict(from_attributes=True)