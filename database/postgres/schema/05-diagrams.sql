-- database/postgres/schema/05-diagrams.sql
-- Diagrams table and related structures
-- COMPLETE AND CORRECTED to match backend/app/models/diagram.py

-- Drop existing tables if exist (for clean reinstall)
DROP TABLE IF EXISTS diagram_elements CASCADE;
DROP TABLE IF EXISTS diagrams CASCADE;

-- Diagrams table - visual projections of semantic models
CREATE TABLE diagrams (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_id UUID NOT NULL REFERENCES models(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- CRITICAL: Column is 'notation' NOT 'notation_type'
    notation diagram_notation NOT NULL,
    
    -- Notation-specific configuration (e.g., swimlane settings, sequence diagram config)
    notation_config JSONB NOT NULL DEFAULT '{}'::JSONB,
    
    -- Array of concept UUIDs that are visible in this diagram
    visible_concepts UUID[] NOT NULL DEFAULT ARRAY[]::UUID[],
    
    -- Additional diagram settings (viewport, zoom, grid, etc.)
    settings JSONB NOT NULL DEFAULT '{}'::JSONB,
    
    -- Is this the default diagram for the model?
    is_default BOOLEAN DEFAULT FALSE NOT NULL,
    
    -- Soft delete support
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    -- Ownership and audit
    created_by UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    updated_by UUID REFERENCES users(id) ON DELETE RESTRICT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    
    -- Constraints
    CONSTRAINT diagrams_name_check CHECK (LENGTH(TRIM(name)) >= 1 AND LENGTH(name) <= 255),
    -- Ensure unique name within model
    CONSTRAINT diagrams_unique_name UNIQUE(model_id, name, deleted_at)
);

-- Diagram elements table (for diagram-specific visual properties)
CREATE TABLE diagram_elements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    diagram_id UUID NOT NULL REFERENCES diagrams(id) ON DELETE CASCADE,
    
    -- Concept ID from semantic model (stored in FalkorDB)
    concept_id UUID NOT NULL,
    
    -- Element type (node, edge, annotation, etc.)
    element_type VARCHAR(100) NOT NULL,
    
    -- Element-specific data (type-specific properties)
    element_data JSONB NOT NULL DEFAULT '{}'::JSONB,
    
    -- Visual properties (color, shape, style, etc.)
    visual_properties JSONB NOT NULL DEFAULT '{}'::JSONB,
    
    -- Position and size (for manual layouts)
    position_x DOUBLE PRECISION,
    position_y DOUBLE PRECISION,
    width DOUBLE PRECISION,
    height DOUBLE PRECISION,
    z_index INTEGER DEFAULT 0,
    
    -- Visibility control
    is_visible BOOLEAN DEFAULT TRUE NOT NULL,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    
    -- Constraints
    CONSTRAINT diagram_elements_element_type_check CHECK (element_type IN (
        'node', 'edge', 'annotation', 'group', 'swimlane', 'pool', 'lane'
    )),
    -- Ensure unique concept per diagram
    CONSTRAINT diagram_elements_unique_concept UNIQUE(diagram_id, concept_id)
);

-- Indexes for diagrams table
CREATE INDEX idx_diagrams_model_id ON diagrams(model_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_diagrams_notation ON diagrams(notation) WHERE deleted_at IS NULL;
CREATE INDEX idx_diagrams_is_default ON diagrams(is_default) WHERE is_default = TRUE AND deleted_at IS NULL;
CREATE INDEX idx_diagrams_created_by ON diagrams(created_by);
CREATE INDEX idx_diagrams_created_at ON diagrams(created_at DESC);
CREATE INDEX idx_diagrams_deleted_at ON diagrams(deleted_at) WHERE deleted_at IS NOT NULL;

-- GIN index for visible_concepts array
CREATE INDEX idx_diagrams_visible_concepts ON diagrams USING GIN(visible_concepts);

-- GIN indexes for JSONB columns
CREATE INDEX idx_diagrams_notation_config ON diagrams USING GIN(notation_config);
CREATE INDEX idx_diagrams_settings ON diagrams USING GIN(settings);

-- Indexes for diagram_elements table
CREATE INDEX idx_diagram_elements_diagram_id ON diagram_elements(diagram_id);
CREATE INDEX idx_diagram_elements_concept_id ON diagram_elements(concept_id);
CREATE INDEX idx_diagram_elements_element_type ON diagram_elements(element_type);
CREATE INDEX idx_diagram_elements_is_visible ON diagram_elements(is_visible) WHERE is_visible = TRUE;
CREATE INDEX idx_diagram_elements_created_at ON diagram_elements(created_at DESC);

-- GIN indexes for JSONB columns
CREATE INDEX idx_diagram_elements_element_data ON diagram_elements USING GIN(element_data);
CREATE INDEX idx_diagram_elements_visual_properties ON diagram_elements USING GIN(visual_properties);

-- Spatial index for position queries (if needed for collision detection)
CREATE INDEX idx_diagram_elements_position ON diagram_elements USING GIST(
    box(point(position_x, position_y), point(position_x + COALESCE(width, 100), position_y + COALESCE(height, 100)))
) WHERE position_x IS NOT NULL AND position_y IS NOT NULL;

-- Trigger to update updated_at timestamp
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
        AND is_default = TRUE;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER ensure_single_default_diagram_trigger
    BEFORE INSERT OR UPDATE OF is_default ON diagrams
    FOR EACH ROW
    WHEN (NEW.is_default = TRUE)
    EXECUTE FUNCTION ensure_single_default_diagram();

-- Function to get diagram with elements
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
    is_visible BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        d.id,
        d.name,
        d.notation,
        de.id,
        de.concept_id,
        de.element_type,
        de.element_data,
        de.visual_properties,
        de.position_x,
        de.position_y,
        de.width,
        de.height,
        de.is_visible
    FROM diagrams d
    LEFT JOIN diagram_elements de ON de.diagram_id = d.id
    WHERE d.id = p_diagram_id
    AND d.deleted_at IS NULL;
END;
$$ LANGUAGE plpgsql STABLE;

-- Function to clone a diagram
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
        RAISE EXCEPTION 'Source diagram not found';
    END IF;
    
    -- Create new diagram with same properties
    INSERT INTO diagrams (
        model_id,
        name,
        description,
        notation,
        notation_config,
        visible_concepts,
        settings,
        is_default,
        created_by
    ) VALUES (
        v_source_diagram.model_id,
        p_new_name,
        v_source_diagram.description,
        v_source_diagram.notation,
        v_source_diagram.notation_config,
        v_source_diagram.visible_concepts,
        v_source_diagram.settings,
        FALSE,
        p_user_id
    )
    RETURNING id INTO v_new_diagram_id;
    
    -- Clone diagram elements
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
        is_visible
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
        is_visible
    FROM diagram_elements
    WHERE diagram_id = p_source_diagram_id;
    
    RETURN v_new_diagram_id;
END;
$$ LANGUAGE plpgsql;

-- Function to get diagrams by model
CREATE OR REPLACE FUNCTION get_diagrams_by_model(p_model_id UUID)
RETURNS TABLE (
    id UUID,
    name VARCHAR(255),
    notation diagram_notation,
    is_default BOOLEAN,
    element_count BIGINT,
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
        COUNT(de.id) as element_count,
        d.created_at,
        d.updated_at
    FROM diagrams d
    LEFT JOIN diagram_elements de ON de.diagram_id = d.id AND de.is_visible = TRUE
    WHERE d.model_id = p_model_id
    AND d.deleted_at IS NULL
    GROUP BY d.id, d.name, d.notation, d.is_default, d.created_at, d.updated_at
    ORDER BY d.is_default DESC, d.created_at DESC;
END;
$$ LANGUAGE plpgsql STABLE;

-- Logging
DO $$
BEGIN
    RAISE NOTICE 'Diagrams schema created successfully';
    RAISE NOTICE '✓ Column: notation (NOT notation_type)';
    RAISE NOTICE '✓ Column: notation_config (JSONB)';
    RAISE NOTICE '✓ Column: visible_concepts (UUID[])';
    RAISE NOTICE '✓ Column: settings (JSONB)';
END $$;