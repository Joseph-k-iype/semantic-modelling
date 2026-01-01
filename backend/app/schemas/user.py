# backend/app/schemas/user.py
"""
User Pydantic schemas - EXACT match to database schema
Path: backend/app/schemas/user.py
"""

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_serializer, computed_field


class UserBase(BaseModel):
    """Base user schema with common fields"""
    email: EmailStr
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    full_name: Optional[str] = Field(None, max_length=255)


class UserCreate(BaseModel):
    """Schema for creating a new user"""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    full_name: Optional[str] = Field(None, max_length=255)


class UserUpdate(BaseModel):
    """Schema for updating user information"""
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    full_name: Optional[str] = Field(None, max_length=255)
    avatar_url: Optional[str] = None
    is_active: Optional[bool] = None


class UserPasswordUpdate(BaseModel):
    """Schema for updating user password"""
    current_password: str = Field(..., min_length=8, max_length=100)
    new_password: str = Field(..., min_length=8, max_length=100)


class UserResponse(BaseModel):
    """
    User response schema (without sensitive data)
    
    EXACT match to database schema
    """
    id: UUID
    email: str
    username: Optional[str] = None
    full_name: Optional[str] = None
    
    # Database uses 'role' column (ADMIN/USER)
    role: str = 'USER'
    
    is_active: bool
    is_verified: bool
    avatar_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None
    email_verified_at: Optional[datetime] = None
    
    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={UUID: str}
    )
    
    @field_serializer('id')
    def serialize_id(self, value: UUID, _info) -> str:
        """Convert UUID to string for JSON serialization"""
        return str(value)
    
    @computed_field
    @property
    def is_superuser(self) -> bool:
        """
        Computed field for backward compatibility
        Database has 'role', frontend expects 'is_superuser'
        """
        return self.role == 'ADMIN'


class UserInDB(UserBase):
    """
    User schema as stored in database
    
    CRITICAL: Matches EXACT database columns
    - password_hash (NOT hashed_password)
    - role (NOT is_superuser)
    """
    id: UUID
    
    # CRITICAL: Database column is 'password_hash'
    password_hash: str
    
    # CRITICAL: Database column is 'role' (ADMIN/USER ENUM)
    role: str = 'USER'
    
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None
    email_verified_at: Optional[datetime] = None
    avatar_url: Optional[str] = None
    preferences: dict = {}
    settings: dict = {}
    deleted_at: Optional[datetime] = None
    
    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={UUID: str}
    )
    
    @field_serializer('id')
    def serialize_id(self, value: UUID, _info) -> str:
        """Convert UUID to string for JSON serialization"""
        return str(value)
    
    @computed_field
    @property
    def is_superuser(self) -> bool:
        """Computed property for backward compatibility"""
        return self.role == 'ADMIN'
    
    @computed_field
    @property
    def hashed_password(self) -> str:
        """Alias for backward compatibility"""
        return self.password_hash