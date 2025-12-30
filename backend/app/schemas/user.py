# backend/app/schemas/user.py
"""
User Pydantic schemas - FIXED to match database column names
Path: backend/app/schemas/user.py
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict


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
    """User response schema (without sensitive data) - FIXED: Use last_login_at"""
    id: str
    email: str
    username: Optional[str] = None
    full_name: Optional[str] = None
    is_active: bool
    is_superuser: bool
    is_verified: bool
    avatar_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None  # FIXED: Changed from last_login
    
    model_config = ConfigDict(from_attributes=True)


class UserInDB(UserBase):
    """User schema as stored in database - FIXED: Use last_login_at"""
    id: str
    hashed_password: str
    is_active: bool
    is_superuser: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None  # FIXED: Changed from last_login
    avatar_url: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)