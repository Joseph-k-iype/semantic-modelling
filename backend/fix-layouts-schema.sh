#!/bin/bash
# backend/fix-layouts-schema-docker.sh
# Script to fix layouts table by removing problematic trigger - DOCKER VERSION
# Path: backend/fix-layouts-schema-docker.sh

set -e

echo "=================================================="
echo "🔧 Fixing Layouts Schema - Removing Trigger"
echo "=================================================="

# Get Docker container name (try common names)
CONTAINER_NAME=""
for name in "modeling-postgres" "postgres" "enterprise-modeling-platform-postgres-1" "enterprise-modeling-platform_postgres_1"; do
    if docker ps --format '{{.Names}}' | grep -q "^${name}$"; then
        CONTAINER_NAME=$name
        break
    fi
done

if [ -z "$CONTAINER_NAME" ]; then
    echo "❌ Error: Could not find PostgreSQL Docker container"
    echo ""
    echo "Available containers:"
    docker ps --format "{{.Names}}"
    echo ""
    echo "Please specify container name manually:"
    echo "  docker-compose exec <postgres-container-name> psql -U dbuser -d modeldb"
    exit 1
fi

echo ""
echo "Found PostgreSQL container: $CONTAINER_NAME"
echo "Database: modeldb"
echo "User: dbuser"
echo ""

# Step 1: Backup existing layouts
echo "Step 1: Creating backup of existing layouts..."
docker exec $CONTAINER_NAME psql -U dbuser -d modeldb <<EOF
CREATE TABLE IF NOT EXISTS layouts_backup_$(date +%Y%m%d) AS 
SELECT * FROM layouts;
EOF

BACKUP_COUNT=$(docker exec $CONTAINER_NAME psql -U dbuser -d modeldb -t -c "SELECT COUNT(*) FROM layouts_backup_$(date +%Y%m%d);")
echo "   ✅ Backed up $BACKUP_COUNT layouts to layouts_backup_$(date +%Y%m%d) table"

# Step 2: Drop the problematic trigger
echo ""
echo "Step 2: Dropping automatic layout creation trigger..."
docker exec $CONTAINER_NAME psql -U dbuser -d modeldb <<EOF
-- Drop trigger if exists
DROP TRIGGER IF EXISTS create_diagram_initial_layout ON diagrams;

-- Drop function if exists
DROP FUNCTION IF EXISTS create_initial_layout();

-- Verify
SELECT 'Trigger removed successfully' as status;
EOF

echo "   ✅ Trigger removed"

# Step 3: Add deleted_at column if not exists
echo ""
echo "Step 3: Adding soft delete support to layouts..."
docker exec $CONTAINER_NAME psql -U dbuser -d modeldb <<EOF
-- Add deleted_at column if not exists
DO \$\$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'layouts' AND column_name = 'deleted_at'
    ) THEN
        ALTER TABLE layouts ADD COLUMN deleted_at TIMESTAMP WITH TIME ZONE;
        CREATE INDEX idx_layouts_deleted_at ON layouts(deleted_at);
    END IF;
END \$\$;

-- Verify
SELECT 'Soft delete support added' as status;
EOF

echo "   ✅ Soft delete support added"

# Step 4: Update view to filter deleted records
echo ""
echo "Step 4: Updating diagrams_with_layouts view..."
docker exec $CONTAINER_NAME psql -U dbuser -d modeldb <<EOF
-- Drop and recreate view
DROP VIEW IF EXISTS diagrams_with_layouts;

CREATE VIEW diagrams_with_layouts AS
SELECT 
    d.id,
    d.model_id,
    d.name,
    d.description,
    d.notation,
    d.visible_concepts,
    d.created_by,
    d.updated_by,
    d.created_at,
    d.updated_at,
    l.id as default_layout_id,
    l.name as default_layout_name,
    l.engine as default_layout_engine,
    COUNT(l_all.id) as layout_count,
    u_created.full_name as created_by_name,
    u_updated.full_name as updated_by_name
FROM diagrams d
LEFT JOIN layouts l ON d.id = l.diagram_id AND l.is_default = TRUE AND l.deleted_at IS NULL
LEFT JOIN layouts l_all ON d.id = l_all.diagram_id AND l_all.deleted_at IS NULL
LEFT JOIN users u_created ON d.created_by = u_created.id
LEFT JOIN users u_updated ON d.updated_by = u_updated.id
WHERE d.deleted_at IS NULL
GROUP BY d.id, l.id, u_created.id, u_updated.id;

-- Verify
SELECT 'View updated successfully' as status;
EOF

echo "   ✅ View updated"

# Step 5: Verify the changes
echo ""
echo "Step 5: Verifying changes..."

TRIGGER_COUNT=$(docker exec $CONTAINER_NAME psql -U dbuser -d modeldb -t -c "
SELECT COUNT(*) 
FROM pg_trigger 
WHERE tgname = 'create_diagram_initial_layout';
")

if [ "$TRIGGER_COUNT" -eq "0" ]; then
    echo "   ✅ Trigger successfully removed"
else
    echo "   ❌ Warning: Trigger still exists"
fi

COLUMN_EXISTS=$(docker exec $CONTAINER_NAME psql -U dbuser -d modeldb -t -c "
SELECT COUNT(*) 
FROM information_schema.columns 
WHERE table_name = 'layouts' 
AND column_name = 'deleted_at';
")

if [ "$COLUMN_EXISTS" -eq "1" ]; then
    echo "   ✅ Soft delete column exists"
else
    echo "   ❌ Warning: Soft delete column not found"
fi

# Summary
echo ""
echo "=================================================="
echo "✅ Layouts Schema Fix Complete!"
echo "=================================================="
echo ""
echo "Summary:"
echo "  - Backed up layouts to layouts_backup_$(date +%Y%m%d) table"
echo "  - Removed automatic trigger"
echo "  - Added soft delete support"
echo "  - Updated view for deleted records"
echo ""
echo "Next steps:"
echo "  1. Restart backend: docker-compose restart backend"
echo "  2. Test diagram creation"
echo "  3. Verify layouts are created correctly"
echo ""
echo "To restore from backup if needed:"
echo "  docker exec $CONTAINER_NAME psql -U dbuser -d modeldb -c 'DELETE FROM layouts; INSERT INTO layouts SELECT * FROM layouts_backup_$(date +%Y%m%d);'"
echo ""