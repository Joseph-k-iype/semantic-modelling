-- database/postgres/schema/07-versions.sql
-- Path: database/postgres/schema/07-versions.sql
-- Model versioning and change tracking - COMPLETE AND FIXED

-- ============================================================================
-- MODEL VERSIONS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS model_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id UUID NOT NULL REFERENCES models(id) ON DELETE CASCADE,
    version INT NOT NULL,
    
    -- Change information
    change_set JSONB NOT NULL,
    change_summary TEXT,
    
    -- Graph snapshot reference
    graph_snapshot_id VARCHAR(255),
    
    -- Version metadata
    created_by UUID NOT NULL REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    -- Tags for this version
    tags TEXT[] DEFAULT ARRAY[]::TEXT[],
    
    CONSTRAINT unique_model_version UNIQUE (model_id, version),
    CONSTRAINT valid_version CHECK (version > 0)
);

-- ============================================================================
-- CHANGE LOG TABLE (granular tracking)
-- ============================================================================
CREATE TABLE IF NOT EXISTS change_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version_id UUID NOT NULL REFERENCES model_versions(id) ON DELETE CASCADE,
    
    -- Change details
    operation VARCHAR(20) NOT NULL, -- create, update, delete
    entity_type VARCHAR(100) NOT NULL, -- concept, relationship, attribute
    entity_id VARCHAR(255) NOT NULL,
    
    -- Old and new values
    old_value JSONB,
    new_value JSONB,
    
    -- Metadata
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    CONSTRAINT valid_operation CHECK (operation IN ('create', 'update', 'delete'))
);

-- ============================================================================
-- VERSION COMPARISONS TABLE (cached diff results)
-- ============================================================================
CREATE TABLE IF NOT EXISTS version_comparisons (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id UUID NOT NULL REFERENCES models(id) ON DELETE CASCADE,
    from_version INT NOT NULL,
    to_version INT NOT NULL,
    
    -- Diff results
    differences JSONB NOT NULL,
    
    -- Computed statistics
    additions_count INT DEFAULT 0,
    modifications_count INT DEFAULT 0,
    deletions_count INT DEFAULT 0,
    
    -- Cache metadata
    computed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    CONSTRAINT unique_version_comparison UNIQUE (model_id, from_version, to_version),
    CONSTRAINT valid_version_range CHECK (from_version < to_version)
);

-- ============================================================================
-- INDEXES
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_model_versions_model_id ON model_versions(model_id);
CREATE INDEX IF NOT EXISTS idx_model_versions_version ON model_versions(model_id, version);
CREATE INDEX IF NOT EXISTS idx_model_versions_created_at ON model_versions(created_at);
CREATE INDEX IF NOT EXISTS idx_model_versions_created_by ON model_versions(created_by);

CREATE INDEX IF NOT EXISTS idx_change_log_version_id ON change_log(version_id);
CREATE INDEX IF NOT EXISTS idx_change_log_entity ON change_log(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_change_log_operation ON change_log(operation);
CREATE INDEX IF NOT EXISTS idx_change_log_changed_at ON change_log(changed_at);

CREATE INDEX IF NOT EXISTS idx_version_comparisons_model_id ON version_comparisons(model_id);
CREATE INDEX IF NOT EXISTS idx_version_comparisons_versions ON version_comparisons(model_id, from_version, to_version);

-- ============================================================================
-- FUNCTIONS AND TRIGGERS
-- ============================================================================

-- Function to auto-increment version number
CREATE OR REPLACE FUNCTION set_next_version_number()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.version IS NULL THEN
        SELECT COALESCE(MAX(version), 0) + 1
        INTO NEW.version
        FROM model_versions
        WHERE model_id = NEW.model_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to set version number automatically
CREATE TRIGGER set_version_number
    BEFORE INSERT ON model_versions
    FOR EACH ROW
    WHEN (NEW.version IS NULL)
    EXECUTE FUNCTION set_next_version_number();

-- Function to update model current version and statistics
-- FIXED: Ensures model_statistics row exists before updating
CREATE OR REPLACE FUNCTION update_model_current_version()
RETURNS TRIGGER AS $$
BEGIN
    -- Update model's current version
    UPDATE models
    SET current_version = NEW.version,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.model_id;
    
    -- Ensure model_statistics row exists (defensive programming)
    INSERT INTO model_statistics (model_id, diagram_count, version_count, concept_count, relationship_count)
    VALUES (NEW.model_id, 0, 0, 0, 0)
    ON CONFLICT (model_id) DO NOTHING;
    
    -- Update version count in statistics
    UPDATE model_statistics
    SET version_count = version_count + 1,
        updated_at = CURRENT_TIMESTAMP
    WHERE model_id = NEW.model_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update current version when new version is created
CREATE TRIGGER update_current_version
    AFTER INSERT ON model_versions
    FOR EACH ROW
    EXECUTE FUNCTION update_model_current_version();

-- ============================================================================
-- VIEWS
-- ============================================================================

-- View for version history with user details
CREATE OR REPLACE VIEW version_history AS
SELECT 
    mv.id,
    mv.model_id,
    mv.version,
    mv.change_summary,
    mv.created_at,
    mv.tags,
    u.full_name as created_by_name,
    u.email as created_by_email,
    (
        SELECT COUNT(*)
        FROM change_log cl
        WHERE cl.version_id = mv.id
    ) as change_count,
    m.name as model_name,
    m.type as model_type,
    m.status as model_status
FROM model_versions mv
LEFT JOIN users u ON mv.created_by = u.id
LEFT JOIN models m ON mv.model_id = m.id
ORDER BY mv.model_id, mv.version DESC;

-- View for latest version of each model
CREATE OR REPLACE VIEW latest_versions AS
SELECT DISTINCT ON (mv.model_id)
    mv.id,
    mv.model_id,
    mv.version,
    mv.change_summary,
    mv.created_at,
    mv.tags,
    u.full_name as created_by_name,
    m.name as model_name,
    m.type as model_type
FROM model_versions mv
LEFT JOIN users u ON mv.created_by = u.id
LEFT JOIN models m ON mv.model_id = m.id
ORDER BY mv.model_id, mv.version DESC;

-- View for version statistics
CREATE OR REPLACE VIEW version_statistics AS
SELECT 
    mv.model_id,
    COUNT(DISTINCT mv.id) as total_versions,
    MAX(mv.version) as latest_version,
    MIN(mv.created_at) as first_version_date,
    MAX(mv.created_at) as latest_version_date,
    COUNT(DISTINCT mv.created_by) as contributor_count,
    (
        SELECT COUNT(*)
        FROM change_log cl
        JOIN model_versions mv2 ON cl.version_id = mv2.id
        WHERE mv2.model_id = mv.model_id
    ) as total_changes
FROM model_versions mv
GROUP BY mv.model_id;

-- ============================================================================
-- COMMENTS
-- ============================================================================
COMMENT ON TABLE model_versions IS 'Version history for models with change tracking';
COMMENT ON TABLE change_log IS 'Granular log of individual changes within each version';
COMMENT ON TABLE version_comparisons IS 'Cached comparison results between versions';

COMMENT ON COLUMN model_versions.change_set IS 'Complete set of changes in this version';
COMMENT ON COLUMN model_versions.graph_snapshot_id IS 'Reference to graph database snapshot';
COMMENT ON COLUMN model_versions.tags IS 'Semantic versioning tags or custom labels';

COMMENT ON COLUMN change_log.operation IS 'Type of change: create, update, or delete';
COMMENT ON COLUMN change_log.entity_type IS 'Type of entity changed: concept, relationship, or attribute';
COMMENT ON COLUMN change_log.old_value IS 'Previous state before change (NULL for create)';
COMMENT ON COLUMN change_log.new_value IS 'New state after change (NULL for delete)';

COMMENT ON COLUMN version_comparisons.differences IS 'Detailed differences between versions';
COMMENT ON COLUMN version_comparisons.computed_at IS 'When this comparison was cached';

COMMENT ON VIEW version_history IS 'Complete version history with user details';
COMMENT ON VIEW latest_versions IS 'Latest version for each model';
COMMENT ON VIEW version_statistics IS 'Aggregated statistics about model versions';