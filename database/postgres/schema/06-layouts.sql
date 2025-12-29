-- database/postgres/schema/06-layouts.sql
-- Layouts table - user-controlled layout configurations

-- Layout engines enum
CREATE TYPE layout_engine AS ENUM ('manual', 'layered', 'force_directed', 
                                    'bpmn_swimlane', 'uml_sequence', 'state_machine');

-- Layouts table - user-controlled layout configurations
CREATE TABLE IF NOT EXISTS layouts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    diagram_id UUID NOT NULL REFERENCES diagrams(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Layout engine used
    engine layout_engine NOT NULL DEFAULT 'manual',
    engine_config JSONB DEFAULT '{}'::JSONB,
    
    -- Node positions and dimensions
    positions JSONB NOT NULL DEFAULT '{}'::JSONB,
    
    -- Layout constraints (pinned nodes, locked sections, etc.)
    constraints JSONB DEFAULT '{}'::JSONB,
    
    -- Whether this is the default layout for the diagram
    is_default BOOLEAN DEFAULT FALSE NOT NULL,
    
    -- Ownership
    created_by UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    CONSTRAINT unique_layout_name_per_diagram UNIQUE (diagram_id, name)
);

-- Indexes
CREATE INDEX idx_layouts_diagram_id ON layouts(diagram_id);
CREATE INDEX idx_layouts_engine ON layouts(engine);
CREATE INDEX idx_layouts_is_default ON layouts(is_default);
CREATE INDEX idx_layouts_created_by ON layouts(created_by);
CREATE INDEX idx_layouts_created_at ON layouts(created_at);

-- Triggers
CREATE TRIGGER update_layouts_updated_at
    BEFORE UPDATE ON layouts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Function to ensure only one default layout per diagram
CREATE OR REPLACE FUNCTION ensure_single_default_layout()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.is_default = TRUE THEN
        -- Unset other default layouts for this diagram
        UPDATE layouts 
        SET is_default = FALSE 
        WHERE diagram_id = NEW.diagram_id 
        AND id != NEW.id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER ensure_default_layout
    BEFORE INSERT OR UPDATE OF is_default ON layouts
    FOR EACH ROW
    WHEN (NEW.is_default = TRUE)
    EXECUTE FUNCTION ensure_single_default_layout();

-- Function to create initial layout when diagram is created
CREATE OR REPLACE FUNCTION create_initial_layout()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO layouts (diagram_id, name, engine, is_default, created_by)
    VALUES (NEW.id, 'Default Layout', 'manual', TRUE, NEW.created_by);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER create_diagram_initial_layout
    AFTER INSERT ON diagrams
    FOR EACH ROW
    EXECUTE FUNCTION create_initial_layout();

-- View for diagrams with layout information
CREATE OR REPLACE VIEW diagrams_with_layouts AS
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
LEFT JOIN layouts l ON d.id = l.diagram_id AND l.is_default = TRUE
LEFT JOIN layouts l_all ON d.id = l_all.diagram_id
LEFT JOIN users u_created ON d.created_by = u_created.id
LEFT JOIN users u_updated ON d.updated_by = u_updated.id
GROUP BY d.id, l.id, u_created.id, u_updated.id;

-- Comments
COMMENT ON TABLE layouts IS 'User-controlled layout configurations - separate from model and diagram';
COMMENT ON COLUMN layouts.positions IS 'JSON object mapping node IDs to {x, y, width, height}';
COMMENT ON COLUMN layouts.constraints IS 'Layout constraints like pinned nodes, locked sections, flow direction';
COMMENT ON COLUMN layouts.is_default IS 'Whether this is the default layout shown when opening the diagram';