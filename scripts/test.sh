#!/bin/bash
# verify-and-fix-user.sh
# Verifies and fixes the User model
# Run from: enterprise-modeling-platform/

set -e

echo "================================"
echo "User Model Fix & Verification"
echo "================================"
echo ""

# Check we're in the right place
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Error: Must run from project root"
    exit 1
fi

USER_FILE="backend/app/models/user.py"

# Backup
echo "📦 Creating backup..."
cp "$USER_FILE" "$USER_FILE.backup-$(date +%Y%m%d-%H%M%S)"
echo "✓ Backup created"
echo ""

# Check if relationship exists
echo "🔍 Checking current user.py..."
if grep -q "created_workspaces" "$USER_FILE"; then
    echo "⚠️  File already has 'created_workspaces' - but might be wrong format"
else
    echo "❌ File is missing 'created_workspaces' relationship"
fi
echo ""

# Create the fixed version
echo "🔧 Writing fixed user.py..."

cat > "$USER_FILE" << 'PYTHON_EOF'
# backend/app/models/user.py
"""
User Database Model - COMPLETE WITH RELATIONSHIPS
Path: backend/app/models/user.py
"""
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text, Enum as SQLEnum, ForeignKey, event
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
import enum

from app.db.base import Base


class UserRole(str, enum.Enum):
    """User role enumeration - MUST match database ENUM 'user_role'"""
    ADMIN = "admin"
    USER = "user"


class User(Base):
    """
    User model for authentication and user management
    
    CRITICAL: Must EXACTLY match database schema
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
            create_type=False,
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
    
    # Audit trail fields
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
    
    # ============================================================================
    # CRITICAL FIX: Relationships for back_populates
    # ============================================================================
    
    # This relationship is REQUIRED by Workspace.creator back_populates
    created_workspaces = relationship(
        "Workspace",
        foreign_keys="Workspace.created_by",
        back_populates="creator"
    )
    
    # ============================================================================
    
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


@event.listens_for(User, 'before_insert')
def receive_before_insert(mapper, connection, target):
    """
    Before insert event - ensure created_by/updated_by are None
    so the database trigger can set them properly
    """
    target.created_by = None
    target.updated_by = None
PYTHON_EOF

echo "✓ Fixed user.py written"
echo ""

# Verify the fix
echo "✅ Verifying fix..."
if grep -q "created_workspaces = relationship" "$USER_FILE"; then
    echo "✓ 'created_workspaces' relationship found!"
else
    echo "❌ ERROR: Relationship still missing!"
    exit 1
fi

# Show the relevant lines
echo ""
echo "📄 Relationship definition:"
grep -A 4 "created_workspaces = relationship" "$USER_FILE"
echo ""

# Remove Python cache
echo "🗑️  Removing Python cache..."
find backend -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find backend -type f -name "*.pyc" -delete 2>/dev/null || true
echo "✓ Cache cleared"
echo ""

# Restart backend
echo "🔄 Restarting backend..."
docker-compose stop backend
sleep 2
docker-compose up -d backend
echo "✓ Backend restarted"
echo ""

# Wait and check
echo "⏳ Waiting for backend to start..."
sleep 8

# Check logs for errors
echo "📋 Checking logs for errors..."
if docker-compose logs --tail=50 backend | grep -i "has no property 'created_workspaces'"; then
    echo ""
    echo "❌ Still has the error!"
    echo ""
    echo "Debug info:"
    echo "  File path: $USER_FILE"
    echo "  File exists: $([ -f "$USER_FILE" ] && echo "YES" || echo "NO")"
    echo ""
    echo "Try:"
    echo "  1. docker-compose down"
    echo "  2. docker-compose up -d"
    echo ""
    exit 1
else
    echo "✓ No relationship errors found!"
fi

# Check if backend is healthy
echo ""
echo "🏥 Checking backend health..."
for i in {1..10}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✓ Backend is healthy!"
        break
    fi
    if [ $i -eq 10 ]; then
        echo "⚠️  Backend not responding on /health"
    fi
    sleep 2
done

echo ""
echo "================================"
echo "✅ Fix Applied!"
echo "================================"
echo ""
echo "Test with:"
echo "  curl -X POST http://localhost:8000/api/v1/auth/register \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"email\":\"test@example.com\",\"username\":\"test\",\"password\":\"Test123!\",\"full_name\":\"Test\"}'"
echo ""
echo "Check logs:"
echo "  docker-compose logs -f backend"
echo ""