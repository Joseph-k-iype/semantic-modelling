"""
Validation Pydantic schemas
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, UUID4, ConfigDict
from enum import Enum


class ValidationSeverity(str, Enum):
    """Validation severity enumeration"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ValidationCategory(str, Enum):
    """Validation category enumeration"""
    SYNTAX = "syntax"
    SEMANTIC = "semantic"
    NOTATION_SPECIFIC = "notation_specific"
    BEST_PRACTICE = "best_practice"


class ValidationMessage(BaseModel):
    """Validation message schema"""
    severity: ValidationSeverity
    category: ValidationCategory
    message: str
    code: str = Field(..., max_length=50)
    element_id: Optional[str] = None
    element_type: Optional[str] = None
    location: Optional[Dict[str, Any]] = None
    suggestions: List[str] = []
    
    model_config = ConfigDict(from_attributes=True)


class ValidationRequest(BaseModel):
    """Schema for validation request"""
    diagram_id: Optional[UUID4] = None
    model_id: Optional[UUID4] = None
    validate_semantics: bool = True
    validate_notation: bool = True
    validate_best_practices: bool = False


class ValidationResponse(BaseModel):
    """Validation response schema"""
    is_valid: bool
    error_count: int = 0
    warning_count: int = 0
    info_count: int = 0
    messages: List[ValidationMessage] = []
    validated_at: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class ValidationRuleConfig(BaseModel):
    """Validation rule configuration"""
    rule_id: str
    enabled: bool = True
    severity: ValidationSeverity = ValidationSeverity.ERROR
    parameters: Dict[str, Any] = {}