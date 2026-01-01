-- database/postgres/schema/05-diagrams.sql
-- Diagrams table and related structures

-- Drop existing tables if exist (for clean reinstall)
DROP TABLE IF EXISTS diagram_elements CASCADE;
DROP TABLE IF EXISTS diagrams CASCADE;

-- Diagrams table (notation-specific projections of semantic models)
CREATE TABLE diagrams (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_id UUID NOT NULL REFERENCES models(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    notation diagram_notation NOT NULL,
    notation_config JSONB DEFAULT '{}'::JSONB,
    visible_concepts UUID[] DEFAULT ARRAY[]::UUID[],
    settings JSONB DEFAULT '{}'::JSONB,
    thumbnail_url TEXT,
    is_default BOOLEAN DEFAULT FALSE NOT NULL,
    deleted_at TIMESTAMP WITH TIME ZONE,
    created_by UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    updated_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    
    -- Constraints
    CONSTRAINT diagrams_name_check CHECK (LENGTH(TRIM(name)) >= 1 AND LENGTH(name) <= 255),
    -- Ensure unique name within model
    CONSTRAINT diagrams_unique_name UNIQUE(model_id, name, deleted_at)
);

-- Diagram elements table (for caching diagram-specific element data)
CREATE TABLE diagram_elements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    diagram_id UUID NOT NULL REFERENCES diagrams(id) ON DELETE CASCADE,
    concept_id UUID NOT NULL,
    element_type VARCHAR(50) NOT NULL,
    element_data JSONB DEFAULT '{}'::JSONB,
    visual_properties JSONB DEFAULT '{}'::JSONB,
    position_x NUMERIC(10,2),
    position_y NUMERIC(10,2),
    width NUMERIC(10,2),
    height NUMERIC(10,2),
    z_index INTEGER DEFAULT 0,
    is_visible BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    
    -- Constraints
    CONSTRAINT diagram_elements_element_type_check CHECK (LENGTH(element_type) >= 1),
    CONSTRAINT diagram_elements_z_index_check CHECK (z_index >= 0),
    -- Ensure unique concept per diagram
    CONSTRAINT diagram_elements_unique_concept UNIQUE(diagram_id, concept_id)
);

-- Indexes for diagrams table
CREATE INDEX idx_diagrams_model_id ON diagrams(model_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_diagrams_notation ON diagrams(notation) WHERE deleted_at IS NULL;
CREATE INDEX idx_diagrams_is_default ON diagrams(is_default) WHERE is_default = TRUE AND deleted_at IS NULL;
CREATE INDEX idx_diagrams_created_by ON diagrams(created_by);
CREATE INDEX idx_diagrams_created_at ON diagrams(created_at DESC);
CREATE INDEX idx_diagrams_updated_at ON diagrams(updated_at DESC);
CREATE INDEX idx_diagrams_deleted_at ON diagrams(deleted_at) WHERE deleted_at IS NOT NULL;
CREATE INDEX idx_diagrams_visible_concepts ON diagrams USING gin(visible_concepts);

-- Full-text search index
CREATE INDEX idx_diagrams_fulltext ON diagrams 
    USING gin(to_tsvector('english', 
        COALESCE(name, '') || ' ' || 
        COALESCE(description, '')
    )) WHERE deleted_at IS NULL;

-- Indexes for diagram_elements table
CREATE INDEX idx_diagram_elements_diagram_id ON diagram_elements(diagram_id);
CREATE INDEX idx_diagram_elements_concept_id ON diagram_elements(concept_id);
CREATE INDEX idx_diagram_elements_element_type ON diagram_elements(element_type);
CREATE INDEX idx_diagram_elements_is_visible ON diagram_elements(is_visible) WHERE is_visible = TRUE;
CREATE INDEX idx_diagram_elements_z_index ON diagram_elements(z_index);
CREATE INDEX idx_diagram_elements_position ON diagram_elements(position_x, position_y);

-- Trigger to update updated_at timestamp
CREATE TRIGGER update_diagrams_updated_at
    BEFORE UPDATE ON diagrams
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_diagram_elements_updated_at
    BEFORE UPDATE ON diagram_elements
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger to increment/decrement diagram count in model_statistics
CREATE OR REPLACE FUNCTION manage_diagram_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        -- Increment diagram count
        PERFORM increment_model_diagram_count(NEW.model_id);
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        -- Decrement diagram count
        PERFORM decrement_model_diagram_count(OLD.model_id);
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER diagram_manage_count_insert
    AFTER INSERT ON diagrams
    FOR EACH ROW
    EXECUTE FUNCTION manage_diagram_count();

CREATE TRIGGER diagram_manage_count_delete
    AFTER DELETE ON diagrams
    FOR EACH ROW
    EXECUTE FUNCTION manage_diagram_count();

-- Trigger to ensure only one default diagram per model
CREATE OR REPLACE FUNCTION ensure_single_default_diagram()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.is_default = TRUE THEN
        -- Set all other diagrams in the model to non-default
        UPDATE diagrams
        SET is_default = FALSE
        WHERE model_id = NEW.model_id
        AND id != NEW.id
        AND is_default = TRUE;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER diagram_ensure_single_default
    AFTER INSERT OR UPDATE OF is_default ON diagrams
    FOR EACH ROW
    WHEN (NEW.is_default = TRUE)
    EXECUTE FUNCTION ensure_single_default_diagram();

-- Trigger to create first diagram as default
CREATE OR REPLACE FUNCTION set_first_diagram_as_default()
RETURNS TRIGGER AS $$
DECLARE
    diagram_count INTEGER;
BEGIN
    -- Count existing diagrams for this model
    SELECT COUNT(*) INTO diagram_count
    FROM diagrams
    WHERE model_id = NEW.model_id
    AND deleted_at IS NULL;
    
    -- If this is the first diagram, make it default
    IF diagram_count = 1 THEN
        NEW.is_default = TRUE;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER diagram_set_first_as_default
    BEFORE INSERT ON diagrams
    FOR EACH ROW
    EXECUTE FUNCTION set_first_diagram_as_default();

-- Function to get diagram with elements
CREATE OR REPLACE FUNCTION get_diagram_with_elements(p_diagram_id UUID)
RETURNS TABLE (
    diagram_id UUID,
    diagram_name VARCHAR(255),
    notation diagram_notation,
    element_id UUID,
    concept_id UUID,
    element_type VARCHAR(50),
    element_data JSONB,
    position_x NUMERIC(10,2),
    position_y NUMERIC(10,2),
    width NUMERIC(10,2),
    height NUMERIC(10,2)
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
        de.position_x,
        de.position_y,
        de.width,
        de.height
    FROM diagrams d
    LEFT JOIN diagram_elements de ON de.diagram_id = d.id AND de.is_visible = TRUE
    WHERE d.id = p_diagram_id
    AND d.deleted_at IS NULL
    ORDER BY de.z_index, de.id;
END;
$$ LANGUAGE plpgsql STABLE;

-- Function to clone diagram
CREATE OR REPLACE FUNCTION clone_diagram(
    p_source_diagram_id UUID,
    p_new_name VARCHAR(255),
    p_user_id UUID
)
RETURNS UUID AS $$
DECLARE
    v_new_diagram_id UUID;
    v_source_diagram RECORD;
BEGIN
    -- Get source diagram
    SELECT * INTO v_source_diagram
    FROM diagrams
    WHERE id = p_source_diagram_id
    AND deleted_at IS NULL;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Source diagram not found';
    END IF;
    
    -- Create new diagram
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
END $$;