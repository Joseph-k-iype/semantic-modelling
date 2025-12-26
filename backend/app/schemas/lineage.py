"""
Lineage and impact analysis Pydantic schemas
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class LineageDirection(str, Enum):
    """Lineage direction enumeration"""
    UPSTREAM = "upstream"  # Dependencies
    DOWNSTREAM = "downstream"  # Dependents
    BOTH = "both"


class LineageNodeType(str, Enum):
    """Lineage node type"""
    CONCEPT = "concept"
    ATTRIBUTE = "attribute"
    RELATIONSHIP = "relationship"
    MODEL = "model"
    DIAGRAM = "diagram"


class LineageNode(BaseModel):
    """Lineage graph node"""
    id: str
    name: str
    type: LineageNodeType
    model_id: Optional[str] = None
    properties: Dict[str, Any] = {}
    
    model_config = ConfigDict(from_attributes=True)


class LineageEdge(BaseModel):
    """Lineage graph edge"""
    source_id: str
    target_id: str
    relationship_type: str
    properties: Dict[str, Any] = {}
    
    model_config = ConfigDict(from_attributes=True)


class LineageRequest(BaseModel):
    """Schema for lineage request"""
    concept_id: str
    direction: LineageDirection = LineageDirection.BOTH
    max_depth: int = Field(default=3, ge=1, le=10)
    include_models: bool = True


class LineageResponse(BaseModel):
    """Lineage graph response"""
    root_node: LineageNode
    nodes: List[LineageNode] = []
    edges: List[LineageEdge] = []
    metadata: Dict[str, Any] = {}
    
    model_config = ConfigDict(from_attributes=True)


class ImpactAnalysisRequest(BaseModel):
    """Schema for impact analysis request"""
    concept_ids: List[str]
    change_type: str = Field(..., max_length=50)  # modify, delete, rename
    max_depth: int = Field(default=5, ge=1, le=10)


class ImpactAnalysisResult(BaseModel):
    """Impact analysis result"""
    affected_concepts: List[LineageNode] = []
    affected_models: List[str] = []
    affected_diagrams: List[str] = []
    severity: str = "low"  # low, medium, high
    recommendations: List[str] = []
    
    model_config = ConfigDict(from_attributes=True)