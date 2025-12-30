# backend/app/models/user.py
"""
User Database Model - FIXED with correct column names matching database schema
Path: backend/app/models/user.py
"""
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.db.base import Base


class User(Base):
    """
    User model for authentication and user management
    
    CRITICAL: Column names MUST match database schema in 01-users.sql
    """
    
    __tablename__ = "users"
    
    # Primary key - UUID type to match PostgreSQL UUID
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    
    # User identity
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    
    # Account status
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # Timestamps - FIXED: Use last_login_at to match database schema
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)  # FIXED: Changed from last_login
    
    # Profile
    avatar_url = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    
    # Preferences stored as JSON
    # Note: preferences column exists in database but we don't map it here
    # to avoid complexity. Can be added later if needed.
    
    # Relationships - defined but not eagerly loaded
    # workspaces = relationship("Workspace", back_populates="owner")
    # models = relationship("Model", back_populates="created_by")
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', username='{self.username}')>"
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': str(self.id),
            'email': self.email,
            'username': self.username,
            'full_name': self.full_name,
            'is_active': self.is_active,
            'is_superuser': self.is_superuser,
            'is_verified': self.is_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None,
            'avatar_url': self.avatar_url,
        }