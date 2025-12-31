-- backend/fix_model_statistics.sql
-- Fix missing model_statistics table
-- Path: backend/fix_model_statistics.sql

-- Drop the problematic trigger first
DROP TRIGGER IF EXISTS update_model_stats_diagram ON diagrams;
DROP FUNCTION IF EXISTS update_model_stats_on_diagram();

-- Create model_statistics table
CREATE TABLE IF NOT EXISTS model_statistics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id UUID NOT NULL UNIQUE REFERENCES models(id) ON DELETE CASCADE,
    
    -- Statistics
    diagram_count INT DEFAULT 0 NOT NULL,
    version_count INT DEFAULT 0 NOT NULL,
    concept_count INT DEFAULT 0 NOT NULL,
    relationship_count INT DEFAULT 0 NOT NULL,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    CONSTRAINT positive_counts CHECK (
        diagram_count >= 0 AND 
        version_count >= 0 AND 
        concept_count >= 0 AND 
        relationship_count >= 0
    )
);

-- Create index
CREATE INDEX IF NOT EXISTS idx_model_statistics_model_id ON model_statistics(model_id);

-- Add trigger for updated_at
CREATE TRIGGER update_model_statistics_updated_at
    BEFORE UPDATE ON model_statistics
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Function to initialize statistics for new models
CREATE OR REPLACE FUNCTION initialize_model_statistics()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO model_statistics (model_id, diagram_count, version_count, concept_count, relationship_count)
    VALUES (NEW.id, 0, 0, 0, 0)
    ON CONFLICT (model_id) DO NOTHING;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to initialize statistics when model is created
CREATE TRIGGER initialize_model_stats
    AFTER INSERT ON models
    FOR EACH ROW
    EXECUTE FUNCTION initialize_model_statistics();

-- Recreate the diagram statistics update function with proper error handling
CREATE OR REPLACE FUNCTION update_model_stats_on_diagram()
RETURNS TRIGGER AS $$
BEGIN
    -- Ensure model_statistics row exists
    INSERT INTO model_statistics (model_id, diagram_count)
    VALUES (COALESCE(NEW.model_id, OLD.model_id), 0)
    ON CONFLICT (model_id) DO NOTHING;
    
    -- Update statistics
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

-- Recreate the trigger
CREATE TRIGGER update_model_stats_diagram
    AFTER INSERT OR DELETE ON diagrams
    FOR EACH ROW
    EXECUTE FUNCTION update_model_stats_on_diagram();

-- Initialize statistics for existing models
INSERT INTO model_statistics (model_id, diagram_count, version_count)
SELECT 
    m.id,
    COUNT(DISTINCT d.id) as diagram_count,
    COUNT(DISTINCT mv.id) as version_count
FROM models m
LEFT JOIN diagrams d ON m.id = d.model_id
LEFT JOIN model_versions mv ON m.id = mv.model_id
GROUP BY m.id
ON CONFLICT (model_id) DO UPDATE
SET 
    diagram_count = EXCLUDED.diagram_count,
    version_count = EXCLUDED.version_count,
    updated_at = CURRENT_TIMESTAMP;

-- Add comments
COMMENT ON TABLE model_statistics IS 'Cached statistics for models to avoid expensive counts';
COMMENT ON COLUMN model_statistics.diagram_count IS 'Number of diagrams for this model';
COMMENT ON COLUMN model_statistics.version_count IS 'Number of versions for this model';
COMMENT ON COLUMN model_statistics.concept_count IS 'Number of concepts in semantic model';
COMMENT ON COLUMN model_statistics.relationship_count IS 'Number of relationships in semantic model';