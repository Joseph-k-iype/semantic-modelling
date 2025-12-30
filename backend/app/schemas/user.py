# backend/app/schemas/user.py
"""
User Pydantic schemas - FIXED with UUID serialization
Path: backend/app/schemas/user.py
"""

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_serializer


class UserBase(BaseModel):
    """Base user schema with common fields"""
    email: EmailStr
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    full_name: Optional[str] = Field(None, max_length=255)


class UserCreate(BaseModel):
    """Schema for creating a new user"""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    full_name: Optional[str] = Field(None, max_length=255)


class UserUpdate(BaseModel):
    """Schema for updating user information"""
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    full_name: Optional[str] = Field(None, max_length=255)
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    is_active: Optional[bool] = None


class UserPasswordUpdate(BaseModel):
    """Schema for updating user password"""
    current_password: str = Field(..., min_length=8, max_length=100)
    new_password: str = Field(..., min_length=8, max_length=100)


class UserResponse(BaseModel):
    """
    User response schema (without sensitive data) - FIXED with UUID serialization
    
    CRITICAL FIX: Added field_serializer to convert UUID to string
    """
    id: UUID  # Changed from str to UUID
    email: str
    username: Optional[str] = None
    full_name: Optional[str] = None
    is_active: bool
    is_superuser: bool
    is_verified: bool
    avatar_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None
    
    # CRITICAL: Configure Pydantic to handle SQLAlchemy models and serialize UUIDs
    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={UUID: str}  # Automatically convert UUID to string in JSON
    )
    
    # CRITICAL: Field serializer to ensure UUID is always converted to string
    @field_serializer('id')
    def serialize_id(self, value: UUID, _info) -> str:
        """Convert UUID to string for JSON serialization"""
        return str(value)


class UserInDB(UserBase):
    """User schema as stored in database - FIXED with UUID"""
    id: UUID  # Changed from str to UUID
    hashed_password: str
    is_active: bool
    is_superuser: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None
    avatar_url: Optional[str] = None
    
    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={UUID: str}
    )
    
    @field_serializer('id')
    def serialize_id(self, value: UUID, _info) -> str:
        """Convert UUID to string for JSON serialization"""
        return str(value)