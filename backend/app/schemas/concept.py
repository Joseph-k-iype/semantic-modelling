"""
Concept Pydantic schemas (for semantic model / graph database)
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class ConceptBase(BaseModel):
    """Base concept schema"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    concept_type: str = Field(..., max_length=50)  # entity, attribute, class, etc.


class ConceptCreate(ConceptBase):
    """Schema for creating a concept"""
    model_id: str  # UUID as string
    properties: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}


class ConceptUpdate(BaseModel):
    """Schema for updating a concept"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class ConceptResponse(ConceptBase):
    """Concept response schema"""
    id: str  # Graph node ID
    model_id: str
    properties: Dict[str, Any]
    metadata: Dict[str, Any]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class ConceptWithRelationships(ConceptResponse):
    """Concept with its relationships"""
    inbound_relationships: List[Any] = []
    outbound_relationships: List[Any] = []
    
    model_config = ConfigDict(from_attributes=True)


class ConceptSearch(BaseModel):
    """Schema for searching concepts"""
    query: str
    model_id: Optional[str] = None
    concept_type: Optional[str] = None
    limit: int = Field(default=20, ge=1, le=100)