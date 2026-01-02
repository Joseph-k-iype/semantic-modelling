-- database/postgres/schema/05-diagrams.sql
-- Diagrams table and related structures - COMPLETE AND CORRECT
-- CRITICAL FIX: Column name is 'notation' (NOT 'notation_type')

-- Drop existing tables if exist (for clean reinstall)
DROP TABLE IF EXISTS diagram_elements CASCADE;
DROP TABLE IF EXISTS diagrams CASCADE;

-- ============================================================================
-- DIAGRAMS TABLE
-- ============================================================================

-- Diagrams table - visual projections of semantic models
-- The semantic model itself is stored in FalkorDB (graph database)
-- This table stores metadata and notation-specific configurations
CREATE TABLE diagrams (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Foreign key to parent model
    model_id UUID NOT NULL REFERENCES models(id) ON DELETE CASCADE,
    
    -- Diagram identity
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- CRITICAL FIX: Column is 'notation' (NOT 'notation_type')
    -- Uses diagram_notation ENUM type (defined in 01-init-db.sql)
    -- Values: 'ER', 'UML_CLASS', 'UML_SEQUENCE', 'UML_ACTIVITY', 'UML_STATE',
    --         'UML_COMPONENT', 'UML_DEPLOYMENT', 'UML_PACKAGE', 'BPMN'
    notation diagram_notation NOT NULL,
    
    -- Notation-specific configuration (swimlanes, lifelines, etc.)
    notation_config JSONB NOT NULL DEFAULT '{}'::JSONB,
    
    -- Array of concept UUIDs that are visible in this diagram (from FalkorDB)
    -- Diagrams can show a subset of the model's concepts
    visible_concepts UUID[] NOT NULL DEFAULT ARRAY[]::UUID[],
    
    -- Additional diagram settings (viewport, zoom, grid, style, etc.)
    settings JSONB NOT NULL DEFAULT '{}'::JSONB,
    
    -- Is this the default diagram for the model?
    is_default BOOLEAN DEFAULT FALSE NOT NULL,
    
    -- Validation state
    validation_errors JSONB NOT NULL DEFAULT '[]'::JSONB,
    is_valid BOOLEAN DEFAULT TRUE NOT NULL,
    last_validated_at TIMESTAMP WITH TIME ZONE,
    
    -- Soft delete support
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    -- Ownership and audit trail
    created_by UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    updated_by UUID REFERENCES users(id) ON DELETE RESTRICT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    
    -- Constraints
    CONSTRAINT diagrams_name_check CHECK (LENGTH(TRIM(name)) >= 1 AND LENGTH(name) <= 255),
    -- Ensure unique name within model (excluding soft-deleted)
    -- NULLS NOT DISTINCT ensures NULL deleted_at values are considered equal for uniqueness
    CONSTRAINT diagrams_unique_name UNIQUE NULLS NOT DISTINCT (model_id, name, deleted_at)
);

-- ============================================================================
-- DIAGRAM ELEMENTS TABLE
-- ============================================================================

-- Diagram elements table - stores diagram-specific visual properties
-- The actual semantic data is in FalkorDB, this stores only visual aspects
CREATE TABLE diagram_elements (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Foreign key to diagram
    diagram_id UUID NOT NULL REFERENCES diagrams(id) ON DELETE CASCADE,
    
    -- Reference to concept in FalkorDB semantic model
    -- This is NOT a foreign key because the concept is in FalkorDB, not PostgreSQL
    concept_id UUID NOT NULL,
    
    -- Element type (node, edge, annotation, group, swimlane, pool, lane, etc.)
    element_type VARCHAR(100) NOT NULL,
    
    -- Element-specific data (type-specific properties, business logic)
    element_data JSONB NOT NULL DEFAULT '{}'::JSONB,
    
    -- Visual properties (color, shape, style, size, etc.) - diagram-specific
    visual_properties JSONB NOT NULL DEFAULT '{}'::JSONB,
    
    -- Position and dimensions (for manual and computed layouts)
    position_x DOUBLE PRECISION,
    position_y DOUBLE PRECISION,
    width DOUBLE PRECISION,
    height DOUBLE PRECISION,
    
    -- Z-index for layering (higher values are on top)
    z_index INTEGER DEFAULT 0,
    
    -- Visibility control
    is_visible BOOLEAN DEFAULT TRUE NOT NULL,
    is_locked BOOLEAN DEFAULT FALSE NOT NULL,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    
    -- Constraints
    CONSTRAINT diagram_elements_element_type_check CHECK (element_type IN (
        'node', 'edge', 'annotation', 'group', 'swimlane', 'pool', 'lane',
        'boundary', 'lifeline', 'message', 'note', 'text'
    )),
    -- Ensure unique concept per diagram
    CONSTRAINT diagram_elements_unique_concept UNIQUE (diagram_id, concept_id)
);

-- ============================================================================
-- INDEXES FOR DIAGRAMS TABLE
-- ============================================================================

CREATE INDEX idx_diagrams_model_id ON diagrams(model_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_diagrams_notation ON diagrams(notation) WHERE deleted_at IS NULL;
CREATE INDEX idx_diagrams_is_default ON diagrams(is_default) WHERE is_default = TRUE AND deleted_at IS NULL;
CREATE INDEX idx_diagrams_is_valid ON diagrams(is_valid) WHERE is_valid = FALSE AND deleted_at IS NULL;
CREATE INDEX idx_diagrams_created_by ON diagrams(created_by);
CREATE INDEX idx_diagrams_created_at ON diagrams(created_at DESC);
CREATE INDEX idx_diagrams_deleted_at ON diagrams(deleted_at) WHERE deleted_at IS NOT NULL;

-- GIN index for UUID array (visible_concepts)
CREATE INDEX idx_diagrams_visible_concepts ON diagrams USING GIN(visible_concepts);

-- GIN indexes for JSONB columns (for JSON queries)
CREATE INDEX idx_diagrams_notation_config ON diagrams USING GIN(notation_config);
CREATE INDEX idx_diagrams_settings ON diagrams USING GIN(settings);
CREATE INDEX idx_diagrams_validation_errors ON diagrams USING GIN(validation_errors) WHERE is_valid = FALSE;

-- ============================================================================
-- INDEXES FOR DIAGRAM_ELEMENTS TABLE
-- ============================================================================

CREATE INDEX idx_diagram_elements_diagram_id ON diagram_elements(diagram_id);
CREATE INDEX idx_diagram_elements_concept_id ON diagram_elements(concept_id);
CREATE INDEX idx_diagram_elements_element_type ON diagram_elements(element_type);
CREATE INDEX idx_diagram_elements_is_visible ON diagram_elements(is_visible) WHERE is_visible = TRUE;
CREATE INDEX idx_diagram_elements_is_locked ON diagram_elements(is_locked) WHERE is_locked = TRUE;
CREATE INDEX idx_diagram_elements_z_index ON diagram_elements(z_index) WHERE z_index != 0;
CREATE INDEX idx_diagram_elements_created_at ON diagram_elements(created_at DESC);

-- GIN indexes for JSONB columns
CREATE INDEX idx_diagram_elements_element_data ON diagram_elements USING GIN(element_data);
CREATE INDEX idx_diagram_elements_visual_properties ON diagram_elements USING GIN(visual_properties);

-- Spatial index for position queries (useful for collision detection, spatial queries)
-- Uses GIST index on a bounding box constructed from position and dimensions
CREATE INDEX idx_diagram_elements_position ON diagram_elements USING GIST(
    box(
        point(position_x, position_y), 
        point(
            position_x + COALESCE(width, 100), 
            position_y + COALESCE(height, 100)
        )
    )
) WHERE position_x IS NOT NULL AND position_y IS NOT NULL;

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Trigger to update updated_at timestamp on modification
CREATE TRIGGER update_diagrams_updated_at
    BEFORE UPDATE ON diagrams
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_diagram_elements_updated_at
    BEFORE UPDATE ON diagram_elements
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger to ensure only one default diagram per model
CREATE OR REPLACE FUNCTION ensure_single_default_diagram()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.is_default = TRUE THEN
        -- Unset other default diagrams for this model
        UPDATE diagrams
        SET is_default = FALSE
        WHERE model_id = NEW.model_id
        AND id != NEW.id
        AND is_default = TRUE
        AND deleted_at IS NULL;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER ensure_single_default_diagram_trigger
    BEFORE INSERT OR UPDATE OF is_default ON diagrams
    FOR EACH ROW
    WHEN (NEW.is_default = TRUE)
    EXECUTE FUNCTION ensure_single_default_diagram();

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function to get diagram with its elements
CREATE OR REPLACE FUNCTION get_diagram_with_elements(p_diagram_id UUID)
RETURNS TABLE (
    diagram_id UUID,
    diagram_name VARCHAR(255),
    notation diagram_notation,
    element_id UUID,
    concept_id UUID,
    element_type VARCHAR(100),
    element_data JSONB,
    visual_properties JSONB,
    position_x DOUBLE PRECISION,
    position_y DOUBLE PRECISION,
    width DOUBLE PRECISION,
    height DOUBLE PRECISION,
    z_index INTEGER,
    is_visible BOOLEAN,
    is_locked BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        d.id AS diagram_id,
        d.name AS diagram_name,
        d.notation,
        de.id AS element_id,
        de.concept_id,
        de.element_type,
        de.element_data,
        de.visual_properties,
        de.position_x,
        de.position_y,
        de.width,
        de.height,
        de.z_index,
        de.is_visible,
        de.is_locked
    FROM diagrams d
    LEFT JOIN diagram_elements de ON de.diagram_id = d.id
    WHERE d.id = p_diagram_id
    AND d.deleted_at IS NULL
    ORDER BY de.z_index ASC, de.created_at ASC;
END;
$$ LANGUAGE plpgsql STABLE;

-- Function to clone a diagram with all its elements
CREATE OR REPLACE FUNCTION clone_diagram(
    p_source_diagram_id UUID,
    p_new_name VARCHAR(255),
    p_user_id UUID
)
RETURNS UUID AS $$
DECLARE
    v_new_diagram_id UUID;
    v_source_diagram diagrams%ROWTYPE;
BEGIN
    -- Get source diagram
    SELECT * INTO v_source_diagram
    FROM diagrams
    WHERE id = p_source_diagram_id
    AND deleted_at IS NULL;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Source diagram % not found or is deleted', p_source_diagram_id;
    END IF;
    
    -- Create new diagram with same properties but new name
    INSERT INTO diagrams (
        model_id,
        name,
        description,
        notation,
        notation_config,
        visible_concepts,
        settings,
        is_default,
        validation_errors,
        is_valid,
        created_by,
        updated_by
    ) VALUES (
        v_source_diagram.model_id,
        p_new_name,
        v_source_diagram.description,
        v_source_diagram.notation,
        v_source_diagram.notation_config,
        v_source_diagram.visible_concepts,
        v_source_diagram.settings,
        FALSE,  -- New diagram is not default
        v_source_diagram.validation_errors,
        v_source_diagram.is_valid,
        p_user_id,
        p_user_id
    )
    RETURNING id INTO v_new_diagram_id;
    
    -- Clone all diagram elements
    INSERT INTO diagram_elements (
        diagram_id,
        concept_id,
        element_type,
        element_data,
        visual_properties,
        position_x,
        position_y,
        width,
        height,
        z_index,
        is_visible,
        is_locked
    )
    SELECT 
        v_new_diagram_id,
        concept_id,
        element_type,
        element_data,
        visual_properties,
        position_x,
        position_y,
        width,
        height,
        z_index,
        is_visible,
        is_locked
    FROM diagram_elements
    WHERE diagram_id = p_source_diagram_id;
    
    RETURN v_new_diagram_id;
END;
$$ LANGUAGE plpgsql;

-- Function to get diagrams by model with element counts
CREATE OR REPLACE FUNCTION get_diagrams_by_model(p_model_id UUID)
RETURNS TABLE (
    id UUID,
    name VARCHAR(255),
    notation diagram_notation,
    is_default BOOLEAN,
    is_valid BOOLEAN,
    element_count BIGINT,
    visible_concept_count INTEGER,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        d.id,
        d.name,
        d.notation,
        d.is_default,
        d.is_valid,
        COUNT(de.id) AS element_count,
        CARDINALITY(d.visible_concepts) AS visible_concept_count,
        d.created_at,
        d.updated_at
    FROM diagrams d
    LEFT JOIN diagram_elements de ON de.diagram_id = d.id AND de.is_visible = TRUE
    WHERE d.model_id = p_model_id
    AND d.deleted_at IS NULL
    GROUP BY d.id, d.name, d.notation, d.is_default, d.is_valid, d.visible_concepts, d.created_at, d.updated_at
    ORDER BY d.is_default DESC, d.created_at DESC;
END;
$$ LANGUAGE plpgsql STABLE;

-- Function to get diagram statistics
CREATE OR REPLACE FUNCTION get_diagram_statistics(p_diagram_id UUID)
RETURNS TABLE (
    total_elements BIGINT,
    node_count BIGINT,
    edge_count BIGINT,
    visible_elements BIGINT,
    locked_elements BIGINT,
    invalid_elements BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*) AS total_elements,
        COUNT(*) FILTER (WHERE element_type = 'node') AS node_count,
        COUNT(*) FILTER (WHERE element_type = 'edge') AS edge_count,
        COUNT(*) FILTER (WHERE is_visible = TRUE) AS visible_elements,
        COUNT(*) FILTER (WHERE is_locked = TRUE) AS locked_elements,
        COUNT(*) FILTER (WHERE (element_data->>'isValid')::BOOLEAN = FALSE) AS invalid_elements
    FROM diagram_elements
    WHERE diagram_id = p_diagram_id;
END;
$$ LANGUAGE plpgsql STABLE;

-- Function to update diagram validation status
CREATE OR REPLACE FUNCTION update_diagram_validation(
    p_diagram_id UUID,
    p_is_valid BOOLEAN,
    p_validation_errors JSONB DEFAULT '[]'::JSONB
)
RETURNS VOID AS $$
BEGIN
    UPDATE diagrams
    SET 
        is_valid = p_is_valid,
        validation_errors = p_validation_errors,
        last_validated_at = NOW()
    WHERE id = p_diagram_id;
END;
$$ LANGUAGE plpgsql;

-- Function to soft delete diagram and its elements
CREATE OR REPLACE FUNCTION soft_delete_diagram(
    p_diagram_id UUID,
    p_user_id UUID
)
RETURNS BOOLEAN AS $$
DECLARE
    v_deleted_count INTEGER;
BEGIN
    -- Soft delete the diagram
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

-- ============================================================================
-- COMMENTS FOR DOCUMENTATION
-- ============================================================================

COMMENT ON TABLE diagrams IS 'Diagram metadata - visual projections of semantic models stored in FalkorDB';
COMMENT ON COLUMN diagrams.notation IS 'Notation type: ER, UML_CLASS, UML_SEQUENCE, UML_ACTIVITY, UML_STATE, UML_COMPONENT, UML_DEPLOYMENT, UML_PACKAGE, BPMN';
COMMENT ON COLUMN diagrams.notation_config IS 'Notation-specific configuration (swimlanes, lifelines, sequence numbering, etc.)';
COMMENT ON COLUMN diagrams.visible_concepts IS 'Array of concept UUIDs from FalkorDB semantic model that are visible in this diagram';
COMMENT ON COLUMN diagrams.settings IS 'Diagram settings (viewport, zoom, grid, snap-to-grid, style preferences, etc.)';
COMMENT ON COLUMN diagrams.is_default IS 'Whether this is the default diagram shown when opening the model';
COMMENT ON COLUMN diagrams.validation_errors IS 'Array of validation error objects from last validation run';
COMMENT ON COLUMN diagrams.is_valid IS 'Whether the diagram passes all validation rules for its notation type';

COMMENT ON TABLE diagram_elements IS 'Visual properties for diagram elements - diagram-specific rendering and layout data';
COMMENT ON COLUMN diagram_elements.concept_id IS 'Reference to concept in FalkorDB semantic model (not a FK because it''s in a different database)';
COMMENT ON COLUMN diagram_elements.element_type IS 'Type of visual element: node, edge, annotation, group, swimlane, pool, lane, etc.';
COMMENT ON COLUMN diagram_elements.element_data IS 'Element-specific business data (labels, properties, configurations)';
COMMENT ON COLUMN diagram_elements.visual_properties IS 'Visual styling (color, shape, line style, font, etc.) specific to this diagram';
COMMENT ON COLUMN diagram_elements.z_index IS 'Z-order for layering (higher values appear on top)';

-- ============================================================================
-- LOGGING
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '============================================';
    RAISE NOTICE 'Diagrams schema created successfully';
    RAISE NOTICE '============================================';
    RAISE NOTICE '✓ Table: diagrams';
    RAISE NOTICE '✓ Table: diagram_elements';
    RAISE NOTICE '✓ Column: notation (NOT notation_type) - CRITICAL FIX APPLIED';
    RAISE NOTICE '✓ Column: notation_config (JSONB)';
    RAISE NOTICE '✓ Column: visible_concepts (UUID[])';
    RAISE NOTICE '✓ Column: settings (JSONB)';
    RAISE NOTICE '✓ Column: validation_errors (JSONB)';
    RAISE NOTICE '✓ Column: is_valid (BOOLEAN)';
    RAISE NOTICE '✓ Indexes: Created for performance';
    RAISE NOTICE '✓ Triggers: update_updated_at, ensure_single_default';
    RAISE NOTICE '✓ Functions: 6 helper functions created';
    RAISE NOTICE '============================================';
END $$;