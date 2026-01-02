# backend/app/models/user.py
"""
User Database Model - COMPLETE with proper created_by/updated_by handling
Path: backend/app/models/user.py

CRITICAL FIXES:
- Uses password_hash (matches database column)
- Uses UserRole enum (matches database ENUM type)
- Properly handles created_by/updated_by (let trigger set them)
- Computed property for is_superuser
"""
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text, Enum as SQLEnum, ForeignKey, event
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Session
import uuid
import enum

from app.db.base import Base


class UserRole(str, enum.Enum):
    """User role enumeration - MUST match database ENUM 'user_role'"""
    ADMIN = "ADMIN"
    USER = "USER"


class User(Base):
    """
    User model for authentication and user management
    
    CRITICAL: Must EXACTLY match database schema in 01-users.sql
    
    Key Points:
    1. Column name is 'password_hash' (NOT hashed_password)
    2. Role uses SQLEnum to match PostgreSQL ENUM type
    3. created_by/updated_by are handled by database trigger
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
    
    # Role - CRITICAL: Must use SQLEnum to match PostgreSQL ENUM type
    role = Column(
        SQLEnum(
            UserRole,
            name="user_role",
            create_type=False,  # Type already exists in database
            native_enum=False,
            values_callable=lambda x: [e.value for e in x]
        ),
        nullable=False,
        default=UserRole.USER,
        index=True
    )
    
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
    
    # CRITICAL: Audit trail fields - database trigger handles these automatically
    # DO NOT set these manually during user creation - let the trigger handle it
    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    updated_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    @property
    def is_superuser(self) -> bool:
        """Computed property: ADMIN role means superuser"""
        return self.role == UserRole.ADMIN
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role.value if isinstance(self.role, UserRole) else self.role}')>"
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': str(self.id),
            'email': self.email,
            'username': self.username,
            'full_name': self.full_name,
            'role': self.role.value if isinstance(self.role, UserRole) else self.role,
            'is_active': self.is_active,
            'is_superuser': self.is_superuser,
            'is_verified': self.is_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None,
            'avatar_url': self.avatar_url,
        }


# Event listener to ensure created_by/updated_by are NOT set before insert
# Let the database trigger handle these fields
@event.listens_for(User, 'before_insert')
def receive_before_insert(mapper, connection, target):
    """
    Before insert event - ensure created_by/updated_by are None
    so the database trigger can set them properly
    """
    # Force these to None so trigger handles them
    target.created_by = None
    target.updated_by = None