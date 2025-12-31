-- database/postgres/schema/05-diagrams.sql
-- Path: database/postgres/schema/05-diagrams.sql
-- FIXED: Properly handle model_statistics updates

-- ============================================================================
-- DIAGRAMS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS diagrams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id UUID NOT NULL REFERENCES models(id) ON DELETE CASCADE,
    
    -- Diagram properties
    name VARCHAR(255) NOT NULL,
    description TEXT,
    notation VARCHAR(50) NOT NULL, -- ER, UML_CLASS, UML_SEQUENCE, BPMN, etc.
    
    -- Visible concepts from the semantic model
    visible_concepts UUID[] DEFAULT '{}', -- Array of concept UUIDs
    
    -- Metadata
    created_by UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    updated_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    CONSTRAINT valid_notation CHECK (notation IN (
        'ER', 'UML_CLASS', 'UML_SEQUENCE', 'UML_ACTIVITY', 
        'UML_STATE_MACHINE', 'UML_COMPONENT', 'UML_DEPLOYMENT', 
        'UML_PACKAGE', 'BPMN', 'CUSTOM'
    ))
);

-- ============================================================================
-- DIAGRAM SNAPSHOTS (for version history)
-- ============================================================================
CREATE TABLE IF NOT EXISTS diagram_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    diagram_id UUID NOT NULL REFERENCES diagrams(id) ON DELETE CASCADE,
    
    -- Snapshot data
    version INT NOT NULL,
    snapshot_data JSONB NOT NULL,
    change_summary TEXT,
    
    -- Metadata
    created_by UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- ============================================================================
-- DIAGRAM VALIDATIONS (cached validation results)
-- ============================================================================
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

-- ============================================================================
-- INDEXES
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_diagrams_model_id ON diagrams(model_id);
CREATE INDEX IF NOT EXISTS idx_diagrams_notation ON diagrams(notation);
CREATE INDEX IF NOT EXISTS idx_diagrams_created_by ON diagrams(created_by);
CREATE INDEX IF NOT EXISTS idx_diagrams_created_at ON diagrams(created_at);
CREATE INDEX IF NOT EXISTS idx_diagrams_updated_at ON diagrams(updated_at);
CREATE INDEX IF NOT EXISTS idx_diagrams_name_search ON diagrams USING gin(to_tsvector('english', name));

CREATE INDEX IF NOT EXISTS idx_diagram_snapshots_diagram_id ON diagram_snapshots(diagram_id);
CREATE INDEX IF NOT EXISTS idx_diagram_snapshots_version ON diagram_snapshots(diagram_id, version);
CREATE INDEX IF NOT EXISTS idx_diagram_snapshots_created_at ON diagram_snapshots(created_at);

CREATE INDEX IF NOT EXISTS idx_diagram_validations_diagram_id ON diagram_validations(diagram_id);
CREATE INDEX IF NOT EXISTS idx_diagram_validations_is_valid ON diagram_validations(is_valid);
CREATE INDEX IF NOT EXISTS idx_diagram_validations_validated_at ON diagram_validations(validated_at);

-- ============================================================================
-- TRIGGERS
-- ============================================================================
CREATE TRIGGER update_diagrams_updated_at
    BEFORE UPDATE ON diagrams
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Function to update model statistics when diagram is modified
-- FIXED: Ensures model_statistics row exists before updating
CREATE OR REPLACE FUNCTION update_model_stats_on_diagram()
RETURNS TRIGGER AS $$
DECLARE
    target_model_id UUID;
BEGIN
    -- Determine which model_id to use
    IF TG_OP = 'DELETE' THEN
        target_model_id := OLD.model_id;
    ELSE
        target_model_id := NEW.model_id;
    END IF;
    
    -- Ensure model_statistics row exists
    INSERT INTO model_statistics (model_id, diagram_count, version_count, concept_count, relationship_count)
    VALUES (target_model_id, 0, 0, 0, 0)
    ON CONFLICT (model_id) DO NOTHING;
    
    -- Update statistics based on operation
    IF TG_OP = 'INSERT' THEN
        UPDATE model_statistics 
        SET diagram_count = diagram_count + 1,
            updated_at = CURRENT_TIMESTAMP
        WHERE model_id = NEW.model_id;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE model_statistics 
        SET diagram_count = GREATEST(diagram_count - 1, 0),
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

-- ============================================================================
-- COMMENTS
-- ============================================================================
COMMENT ON TABLE diagrams IS 'Visual projections of semantic models - diagrams never store semantics';
COMMENT ON TABLE diagram_snapshots IS 'Version history snapshots of diagrams';
COMMENT ON TABLE diagram_validations IS 'Cached validation results for diagrams';
COMMENT ON COLUMN diagrams.visible_concepts IS 'Array of concept UUIDs from the model that are visible in this diagram';