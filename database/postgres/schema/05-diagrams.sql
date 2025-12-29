-- database/postgres/schema/05-diagrams.sql
-- Diagrams table - visual projections of semantic models

-- Diagrams table
CREATE TABLE IF NOT EXISTS diagrams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id UUID NOT NULL REFERENCES models(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Notation configuration
    notation VARCHAR(100) NOT NULL, -- er, uml_class, bpmn, etc.
    notation_config JSONB DEFAULT '{}'::JSONB,
    
    -- Which concepts from the model are visible in this diagram
    visible_concepts UUID[] DEFAULT ARRAY[]::UUID[],
    
    -- Diagram-specific settings
    settings JSONB DEFAULT '{}'::JSONB,
    
    -- Ownership
    created_by UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    updated_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    CONSTRAINT unique_diagram_name_per_model UNIQUE (model_id, name)
);

-- Diagram snapshots for version history
CREATE TABLE IF NOT EXISTS diagram_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    diagram_id UUID NOT NULL REFERENCES diagrams(id) ON DELETE CASCADE,
    version INT NOT NULL,
    snapshot_data JSONB NOT NULL,
    layout_snapshot JSONB,
    created_by UUID NOT NULL REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    message TEXT,
    
    CONSTRAINT unique_diagram_version UNIQUE (diagram_id, version),
    CONSTRAINT valid_version CHECK (version > 0)
);

-- Diagram validation results cache
CREATE TABLE IF NOT EXISTS diagram_validations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    diagram_id UUID NOT NULL REFERENCES diagrams(id) ON DELETE CASCADE,
    validation_results JSONB NOT NULL,
    is_valid BOOLEAN NOT NULL,
    error_count INT DEFAULT 0,
    warning_count INT DEFAULT 0,
    validated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    -- Index on diagram_id to get latest validation quickly
    CONSTRAINT unique_diagram_validation UNIQUE (diagram_id)
);

-- Indexes
CREATE INDEX idx_diagrams_model_id ON diagrams(model_id);
CREATE INDEX idx_diagrams_notation ON diagrams(notation);
CREATE INDEX idx_diagrams_created_by ON diagrams(created_by);
CREATE INDEX idx_diagrams_created_at ON diagrams(created_at);
CREATE INDEX idx_diagrams_updated_at ON diagrams(updated_at);
CREATE INDEX idx_diagrams_name_search ON diagrams USING gin(to_tsvector('english', name));

CREATE INDEX idx_diagram_snapshots_diagram_id ON diagram_snapshots(diagram_id);
CREATE INDEX idx_diagram_snapshots_version ON diagram_snapshots(diagram_id, version);
CREATE INDEX idx_diagram_snapshots_created_at ON diagram_snapshots(created_at);

CREATE INDEX idx_diagram_validations_diagram_id ON diagram_validations(diagram_id);
CREATE INDEX idx_diagram_validations_is_valid ON diagram_validations(is_valid);
CREATE INDEX idx_diagram_validations_validated_at ON diagram_validations(validated_at);

-- Triggers
CREATE TRIGGER update_diagrams_updated_at
    BEFORE UPDATE ON diagrams
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Function to update model statistics when diagram is modified
CREATE OR REPLACE FUNCTION update_model_stats_on_diagram()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE model_statistics 
        SET diagram_count = diagram_count + 1,
            updated_at = CURRENT_TIMESTAMP
        WHERE model_id = NEW.model_id;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE model_statistics 
        SET diagram_count = diagram_count - 1,
            updated_at = CURRENT_TIMESTAMP
        WHERE model_id = OLD.model_id;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_model_stats_diagram
    AFTER INSERT OR DELETE ON diagrams
    FOR EACH ROW
    EXECUTE FUNCTION update_model_stats_on_diagram();

-- Comments
COMMENT ON TABLE diagrams IS 'Visual projections of semantic models - diagrams never store semantics';
COMMENT ON TABLE diagram_snapshots IS 'Version history snapshots of diagrams';
COMMENT ON TABLE diagram_validations IS 'Cached validation results for diagrams';

COMMENT ON COLUMN diagrams.visible_concepts IS 'Array of concept UUIDs from the model that are visible in this diagram';