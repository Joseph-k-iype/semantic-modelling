-- database/postgres/schema/05-diagrams.sql
-- Complete Diagrams Schema for Semantic Architect
-- This file creates the complete diagrams table with all necessary columns

-- Drop existing tables if they exist (for clean reinstall)
DROP TABLE IF EXISTS diagram_elements CASCADE;
DROP TABLE IF EXISTS diagrams CASCADE;

-- ============================================================================
-- DIAGRAMS TABLE - COMPLETE
-- ============================================================================

CREATE TABLE diagrams (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Foreign key to parent model (nullable for standalone diagrams)
    model_id UUID REFERENCES models(id) ON DELETE CASCADE,
    
    -- Basic information
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Workspace reference (denormalized for easier queries)
    workspace_name VARCHAR(255),
    
    -- Notation - always UML_CLASS for Semantic Architect
    notation VARCHAR(50) NOT NULL DEFAULT 'UML_CLASS',
    
    -- FalkorDB graph reference
    -- Format: {workspace_name}/{diagram_name}/{username}
    -- Example: engineering_workspace/customer_order_diagram/john_doe
    graph_name VARCHAR(500) UNIQUE,
    
    -- Publishing
    is_published BOOLEAN DEFAULT FALSE NOT NULL,
    published_at TIMESTAMP WITH TIME ZONE,
    
    -- Notation-specific configuration (swimlanes, lifelines, etc.)
    notation_config JSONB NOT NULL DEFAULT '{}'::JSONB,
    
    -- Visual settings (viewport, zoom, nodes, edges, etc.)
    settings JSONB NOT NULL DEFAULT '{}'::JSONB,
    
    -- Flags
    is_default BOOLEAN DEFAULT FALSE NOT NULL,
    is_valid BOOLEAN DEFAULT TRUE NOT NULL,
    
    -- Validation
    validation_errors JSONB NOT NULL DEFAULT '[]'::JSONB,
    last_validated_at TIMESTAMP WITH TIME ZONE,
    
    -- Soft delete support
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    -- Audit trail
    created_by UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    updated_by UUID REFERENCES users(id) ON DELETE RESTRICT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    
    -- Constraints
    CONSTRAINT diagrams_name_check CHECK (LENGTH(TRIM(name)) >= 1 AND LENGTH(name) <= 255),
    CONSTRAINT diagrams_unique_name UNIQUE NULLS NOT DISTINCT (model_id, name, deleted_at)
);

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Index for model lookups
CREATE INDEX idx_diagrams_model_id ON diagrams(model_id) WHERE deleted_at IS NULL;

-- Index for notation queries
CREATE INDEX idx_diagrams_notation ON diagrams(notation) WHERE deleted_at IS NULL;

-- Index for graph name lookups
CREATE INDEX idx_diagrams_graph_name ON diagrams(graph_name) WHERE graph_name IS NOT NULL;

-- Index for published diagrams (critical for homepage)
CREATE INDEX idx_diagrams_published ON diagrams(is_published, published_at DESC) 
WHERE is_published = TRUE AND deleted_at IS NULL;

-- Index for workspace lookups
CREATE INDEX idx_diagrams_workspace ON diagrams(workspace_name) 
WHERE workspace_name IS NOT NULL;

-- Index for user's diagrams
CREATE INDEX idx_diagrams_created_by ON diagrams(created_by) WHERE deleted_at IS NULL;

-- Index for soft-deleted diagrams
CREATE INDEX idx_diagrams_deleted_at ON diagrams(deleted_at) WHERE deleted_at IS NOT NULL;

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_diagrams_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_diagrams_updated_at
    BEFORE UPDATE ON diagrams
    FOR EACH ROW
    EXECUTE FUNCTION update_diagrams_updated_at();

-- Trigger to ensure only one default diagram per model
CREATE OR REPLACE FUNCTION ensure_single_default_diagram()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.is_default = TRUE AND NEW.model_id IS NOT NULL THEN
        UPDATE diagrams
        SET is_default = FALSE
        WHERE model_id = NEW.model_id
        AND id != NEW.id
        AND is_default = TRUE;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_ensure_single_default_diagram
    AFTER INSERT OR UPDATE OF is_default ON diagrams
    FOR EACH ROW
    WHEN (NEW.is_default = TRUE)
    EXECUTE FUNCTION ensure_single_default_diagram();

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function to get diagram statistics
CREATE OR REPLACE FUNCTION get_diagram_stats(p_diagram_id UUID)
RETURNS TABLE(
    total_nodes INTEGER,
    total_edges INTEGER,
    total_classes INTEGER,
    total_interfaces INTEGER,
    total_objects INTEGER,
    total_enumerations INTEGER,
    total_packages INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        (settings->'nodes'->0 IS NOT NULL)::INTEGER AS total_nodes,
        (settings->'edges'->0 IS NOT NULL)::INTEGER AS total_edges,
        (SELECT COUNT(*) FROM jsonb_array_elements(settings->'nodes') 
         WHERE value->>'type' = 'class')::INTEGER AS total_classes,
        (SELECT COUNT(*) FROM jsonb_array_elements(settings->'nodes') 
         WHERE value->>'type' = 'interface')::INTEGER AS total_interfaces,
        (SELECT COUNT(*) FROM jsonb_array_elements(settings->'nodes') 
         WHERE value->>'type' = 'object')::INTEGER AS total_objects,
        (SELECT COUNT(*) FROM jsonb_array_elements(settings->'nodes') 
         WHERE value->>'type' = 'enumeration')::INTEGER AS total_enumerations,
        (SELECT COUNT(*) FROM jsonb_array_elements(settings->'nodes') 
         WHERE value->>'type' = 'package')::INTEGER AS total_packages
    FROM diagrams
    WHERE id = p_diagram_id;
END;
$$ LANGUAGE plpgsql STABLE;

-- Function to soft delete diagram
CREATE OR REPLACE FUNCTION soft_delete_diagram(
    p_diagram_id UUID,
    p_user_id UUID
)
RETURNS BOOLEAN AS $$
DECLARE
    v_deleted_count INTEGER;
BEGIN
    UPDATE diagrams
    SET 
        deleted_at = NOW(),
        updated_by = p_user_id,
        updated_at = NOW()
    WHERE id = p_diagram_id
    AND deleted_at IS NULL;
    
    GET DIAGNOSTICS v_deleted_count = ROW_COUNT;
    
    RETURN v_deleted_count > 0;
END;
$$ LANGUAGE plpgsql;

-- Function to publish diagram
CREATE OR REPLACE FUNCTION publish_diagram(
    p_diagram_id UUID,
    p_user_id UUID
)
RETURNS BOOLEAN AS $$
DECLARE
    v_updated_count INTEGER;
BEGIN
    UPDATE diagrams
    SET 
        is_published = TRUE,
        published_at = NOW(),
        updated_by = p_user_id,
        updated_at = NOW()
    WHERE id = p_diagram_id
    AND deleted_at IS NULL;
    
    GET DIAGNOSTICS v_updated_count = ROW_COUNT;
    
    RETURN v_updated_count > 0;
END;
$$ LANGUAGE plpgsql;

-- Function to unpublish diagram
CREATE OR REPLACE FUNCTION unpublish_diagram(
    p_diagram_id UUID,
    p_user_id UUID
)
RETURNS BOOLEAN AS $$
DECLARE
    v_updated_count INTEGER;
BEGIN
    UPDATE diagrams
    SET 
        is_published = FALSE,
        updated_by = p_user_id,
        updated_at = NOW()
    WHERE id = p_diagram_id
    AND deleted_at IS NULL;
    
    GET DIAGNOSTICS v_updated_count = ROW_COUNT;
    
    RETURN v_updated_count > 0;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- COMMENTS FOR DOCUMENTATION
-- ============================================================================

COMMENT ON TABLE diagrams IS 'Diagram metadata - visual projections of semantic models stored in FalkorDB';
COMMENT ON COLUMN diagrams.id IS 'Primary key UUID';
COMMENT ON COLUMN diagrams.model_id IS 'Foreign key to parent model (nullable for standalone diagrams)';
COMMENT ON COLUMN diagrams.name IS 'Diagram name (must be unique within model)';
COMMENT ON COLUMN diagrams.description IS 'Optional diagram description';
COMMENT ON COLUMN diagrams.workspace_name IS 'Workspace name for grouping diagrams (denormalized for easier queries)';
COMMENT ON COLUMN diagrams.notation IS 'Notation type - always UML_CLASS for Semantic Architect';
COMMENT ON COLUMN diagrams.graph_name IS 'FalkorDB graph reference (format: {workspace}/{diagram}/{user}) - one graph per diagram for complete isolation';
COMMENT ON COLUMN diagrams.is_published IS 'Whether this diagram is published to the public library on homepage';
COMMENT ON COLUMN diagrams.published_at IS 'Timestamp when diagram was published';
COMMENT ON COLUMN diagrams.notation_config IS 'Notation-specific configuration (swimlanes, lifelines, sequence numbering, etc.)';
COMMENT ON COLUMN diagrams.settings IS 'Diagram settings including nodes, edges, viewport, zoom, grid, snap-to-grid, style preferences, etc.';
COMMENT ON COLUMN diagrams.is_default IS 'Whether this is the default diagram shown when opening the model';
COMMENT ON COLUMN diagrams.is_valid IS 'Whether the diagram passes all validation rules for its notation type';
COMMENT ON COLUMN diagrams.validation_errors IS 'Array of validation error objects from last validation run';
COMMENT ON COLUMN diagrams.last_validated_at IS 'Timestamp of last validation check';
COMMENT ON COLUMN diagrams.deleted_at IS 'Soft delete timestamp (NULL if not deleted)';
COMMENT ON COLUMN diagrams.created_by IS 'User who created the diagram';
COMMENT ON COLUMN diagrams.updated_by IS 'User who last updated the diagram';
COMMENT ON COLUMN diagrams.created_at IS 'Creation timestamp';
COMMENT ON COLUMN diagrams.updated_at IS 'Last update timestamp (auto-updated by trigger)';

-- ============================================================================
-- SEED DATA (Optional - for testing)
-- ============================================================================

-- Example: Create a sample published diagram (commented out by default)
/*
INSERT INTO diagrams (
    name,
    workspace_name,
    notation,
    graph_name,
    is_published,
    published_at,
    settings,
    created_by
) VALUES (
    'Enterprise Logical Diagram',
    'Engineering',
    'UML_CLASS',
    'engineering/enterprise_logical_diagram/admin',
    TRUE,
    NOW(),
    '{
        "nodes": [
            {
                "id": "node_1",
                "type": "class",
                "position": {"x": 100, "y": 100},
                "data": {
                    "label": "Employee",
                    "type": "class",
                    "color": "#059669",
                    "stereotype": "Entity",
                    "attributes": [
                        {"id": "attr_1", "name": "id", "dataType": "INTEGER", "key": "PRIMARY KEY"},
                        {"id": "attr_2", "name": "name", "dataType": "VARCHAR", "key": "Default"}
                    ]
                }
            }
        ],
        "edges": [],
        "viewport": {"x": 0, "y": 0, "zoom": 1}
    }'::JSONB,
    (SELECT id FROM users WHERE username = 'admin' LIMIT 1)
)
ON CONFLICT DO NOTHING;
*/

-- ============================================================================
-- LOGGING
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '============================================';
    RAISE NOTICE 'Diagrams schema created successfully';
    RAISE NOTICE '============================================';
    RAISE NOTICE '✓ Table: diagrams (with all columns)';
    RAISE NOTICE '✓ Column: name (VARCHAR 255) - NOT NULL';
    RAISE NOTICE '✓ Column: workspace_name (VARCHAR 255)';
    RAISE NOTICE '✓ Column: notation (VARCHAR 50) - DEFAULT UML_CLASS';
    RAISE NOTICE '✓ Column: graph_name (VARCHAR 500) - UNIQUE';
    RAISE NOTICE '✓ Column: is_published (BOOLEAN) - DEFAULT FALSE';
    RAISE NOTICE '✓ Column: published_at (TIMESTAMP)';
    RAISE NOTICE '✓ Column: settings (JSONB) - stores nodes, edges, viewport';
    RAISE NOTICE '✓ Indexes: 8 indexes created for performance';
    RAISE NOTICE '✓ Triggers: update_updated_at, ensure_single_default';
    RAISE NOTICE '✓ Functions: 5 helper functions created';
    RAISE NOTICE '============================================';
    RAISE NOTICE 'ARCHITECTURE: One FalkorDB graph per diagram';
    RAISE NOTICE 'Graph naming: {workspace}/{diagram}/{user}';
    RAISE NOTICE '============================================';
END $$;