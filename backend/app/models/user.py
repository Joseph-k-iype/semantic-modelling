# backend/app/models/user.py
"""
User Database Model - EXACT match to database schema
Path: backend/app/models/user.py
"""
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

from app.db.base import Base


class User(Base):
    """
    User model for authentication and user management
    
    CRITICAL: Must EXACTLY match database schema in 01-users.sql
    
    Database columns:
    - role (user_role ENUM: 'ADMIN' or 'USER') - NOT is_superuser!
    - password_hash (NOT hashed_password!)
    """
    
    __tablename__ = "users"
    
    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    
    # User identity
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=True)
    
    # Password - CRITICAL: Database column is 'password_hash'
    password_hash = Column(String(255), nullable=False)
    
    # Role - CRITICAL: Database uses 'role' ENUM, not 'is_superuser' boolean
    # Values: 'ADMIN' or 'USER'
    role = Column(String(10), nullable=False, default='USER', index=True)
    
    # Account status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_verified = Column(Boolean, default=False, nullable=False, index=True)
    
    # Timestamps
    email_verified_at = Column(DateTime, nullable=True)
    last_login_at = Column(DateTime, nullable=True)
    deleted_at = Column(DateTime, nullable=True, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Profile
    avatar_url = Column(Text, nullable=True)
    
    # Settings stored as JSONB
    preferences = Column(JSONB, nullable=False, default=dict, server_default='{}')
    settings = Column(JSONB, nullable=False, default=dict, server_default='{}')
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': str(self.id),
            'email': self.email,
            'username': self.username,
            'full_name': self.full_name,
            'role': self.role,
            'is_active': self.is_active,
            'is_superuser': self.is_superuser,  # Computed property
            'is_verified': self.is_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None,
            'email_verified_at': self.email_verified_at.isoformat() if self.email_verified_at else None,
            'avatar_url': self.avatar_url,
        }
    
    # ========================================================================
    # BACKWARD COMPATIBILITY PROPERTIES
    # ========================================================================
    
    @property
    def is_superuser(self) -> bool:
        """
        Backward compatibility property
        Database uses 'role' column, but old code expects 'is_superuser'
        """
        return self.role == 'ADMIN'
    
    @is_superuser.setter
    def is_superuser(self, value: bool):
        """Set role based on is_superuser boolean"""
        self.role = 'ADMIN' if value else 'USER'
    
    @property
    def hashed_password(self) -> str:
        """
        Backward compatibility property
        Database column is 'password_hash', old code uses 'hashed_password'
        """
        return self.password_hash
    
    @hashed_password.setter
    def hashed_password(self, value: str):
        """Setter for backward compatibility"""
        self.password_hash = value