# backend/app/models/user.py
"""
User Database Model - FIXED with consistent UUID type
Path: backend/app/models/user.py
"""
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.orm import relationship
import uuid

from app.db.base import Base


class User(Base):
    """User model - FIXED to use String(36) for UUID consistency"""
    
    __tablename__ = "users"
    
    # FIXED: Changed from Integer to String(36) to match UUID in SQL schema
    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    
    # User identity
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    
    # Account status
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=True, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Profile
    avatar_url = Column(String(500), nullable=True)
    
    # Relationships are defined but we don't eagerly load them to avoid circular imports
    # They will be properly established when other models import this
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', username='{self.username}')>"