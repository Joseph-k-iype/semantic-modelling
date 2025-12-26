"""
Relationship Pydantic schemas (for semantic model / graph database)
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class RelationshipBase(BaseModel):
    """Base relationship schema"""
    relationship_type: str = Field(..., max_length=100)
    description: Optional[str] = None


class RelationshipCreate(RelationshipBase):
    """Schema for creating a relationship"""
    source_concept_id: str  # Graph node ID
    target_concept_id: str  # Graph node ID
    properties: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}


class RelationshipUpdate(BaseModel):
    """Schema for updating a relationship"""
    relationship_type: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class RelationshipResponse(RelationshipBase):
    """Relationship response schema"""
    id: str  # Graph edge ID
    source_concept_id: str
    target_concept_id: str
    properties: Dict[str, Any]
    metadata: Dict[str, Any]
    
    model_config = ConfigDict(from_attributes=True)


class RelationshipWithConcepts(RelationshipResponse):
    """Relationship with source and target concepts"""
    source_concept: Optional[Any] = None
    target_concept: Optional[Any] = None
    
    model_config = ConfigDict(from_attributes=True)