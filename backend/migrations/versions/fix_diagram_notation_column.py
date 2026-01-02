# backend/migrations/versions/fix_diagram_notation_column.py
"""
Fix diagram notation column name

Revision ID: fix_notation_column
Revises: 
Create Date: 2025-01-01 00:00:00.000000

CRITICAL FIX: Renames 'notation_type' column to 'notation' in diagrams table
to match the SQL schema and model definition.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'fix_notation_column'
down_revision = None  # Update this to your last migration
branch_labels = None
depends_on = None


def upgrade():
    """
    Upgrade database schema
    
    Renames 'notation_type' to 'notation' if it exists
    """
    # First check if notation_type column exists and notation doesn't
    conn = op.get_bind()
    
    # Check current columns in diagrams table
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('diagrams')]
    
    if 'notation_type' in columns and 'notation' not in columns:
        # Rename notation_type to notation
        op.alter_column(
            'diagrams',
            'notation_type',
            new_column_name='notation',
            existing_type=sa.String(50),
            existing_nullable=False
        )
        print("✅ Renamed 'notation_type' to 'notation' in diagrams table")
    elif 'notation' in columns:
        print("✅ Column 'notation' already exists, no change needed")
    else:
        print("⚠️  Neither 'notation_type' nor 'notation' found - this might be a fresh install")


def downgrade():
    """
    Downgrade database schema
    
    Renames 'notation' back to 'notation_type'
    """
    # Check current columns
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('diagrams')]
    
    if 'notation' in columns and 'notation_type' not in columns:
        # Rename notation back to notation_type
        op.alter_column(
            'diagrams',
            'notation',
            new_column_name='notation_type',
            existing_type=sa.String(50),
            existing_nullable=False
        )
        print("✅ Renamed 'notation' back to 'notation_type' in diagrams table")