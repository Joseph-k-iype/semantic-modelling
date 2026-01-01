-- database/postgres/schema/04-models.sql
-- Models table and related structures including model_statistics

-- Drop existing tables if exist (for clean reinstall)
DROP TABLE IF EXISTS model_tags CASCADE;
DROP TABLE IF EXISTS model_statistics CASCADE;
DROP TABLE IF EXISTS models CASCADE;

-- Models table (semantic models are stored in graph DB, this is metadata)
CREATE TABLE models (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    folder_id UUID REFERENCES folders(id) ON DELETE SET NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    model_type VARCHAR(50) NOT NULL,
    graph_id VARCHAR(255) UNIQUE NOT NULL,
    metadata JSONB DEFAULT '{}'::JSONB,
    settings JSONB DEFAULT '{}'::JSONB,
    validation_rules JSONB DEFAULT '[]'::JSONB,
    is_published BOOLEAN DEFAULT FALSE NOT NULL,
    published_at TIMESTAMP WITH TIME ZONE,
    published_version VARCHAR(20),
    deleted_at TIMESTAMP WITH TIME ZONE,
    created_by UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    updated_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    
    -- Constraints
    CONSTRAINT models_name_check CHECK (LENGTH(TRIM(name)) >= 1 AND LENGTH(name) <= 255),
    CONSTRAINT models_model_type_check CHECK (model_type IN (
        'ER',
        'UML_CLASS',
        'UML_SEQUENCE',
        'UML_ACTIVITY',
        'UML_STATE',
        'UML_COMPONENT',
        'UML_DEPLOYMENT',
        'UML_PACKAGE',
        'BPMN',
        'MIXED'
    )),
    CONSTRAINT models_graph_id_check CHECK (LENGTH(graph_id) >= 1),
    -- Ensure unique name within workspace and folder
    CONSTRAINT models_unique_name UNIQUE(workspace_id, folder_id, name, deleted_at)
);

-- Model statistics table (denormalized for performance)
CREATE TABLE model_statistics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_id UUID UNIQUE NOT NULL REFERENCES models(id) ON DELETE CASCADE,
    total_concepts INTEGER DEFAULT 0 NOT NULL,
    total_relationships INTEGER DEFAULT 0 NOT NULL,
    total_diagrams INTEGER DEFAULT 0 NOT NULL,
    total_versions INTEGER DEFAULT 1 NOT NULL,
    last_modified_by UUID REFERENCES users(id) ON DELETE SET NULL,
    last_validation_at TIMESTAMP WITH TIME ZONE,
    validation_status VARCHAR(20) DEFAULT 'PENDING',
    validation_errors INTEGER DEFAULT 0 NOT NULL,
    validation_warnings INTEGER DEFAULT 0 NOT NULL,
    complexity_score NUMERIC(5,2),
    metadata JSONB DEFAULT '{}'::JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    
    -- Constraints
    CONSTRAINT model_statistics_total_concepts_check CHECK (total_concepts >= 0),
    CONSTRAINT model_statistics_total_relationships_check CHECK (total_relationships >= 0),
    CONSTRAINT model_statistics_total_diagrams_check CHECK (total_diagrams >= 0),
    CONSTRAINT model_statistics_total_versions_check CHECK (total_versions >= 0),
    CONSTRAINT model_statistics_validation_errors_check CHECK (validation_errors >= 0),
    CONSTRAINT model_statistics_validation_warnings_check CHECK (validation_warnings >= 0),
    CONSTRAINT model_statistics_validation_status_check CHECK (validation_status IN (
        'PENDING',
        'VALIDATING',
        'VALID',
        'INVALID',
        'ERROR'
    ))
);

-- Model tags table (for categorization)
CREATE TABLE model_tags (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_id UUID NOT NULL REFERENCES models(id) ON DELETE CASCADE,
    tag VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    
    -- Constraints
    CONSTRAINT model_tags_tag_check CHECK (LENGTH(TRIM(tag)) >= 1 AND LENGTH(tag) <= 50),
    CONSTRAINT model_tags_unique UNIQUE(model_id, tag)
);

-- Indexes for models table
CREATE INDEX idx_models_workspace_id ON models(workspace_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_models_folder_id ON models(folder_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_models_model_type ON models(model_type) WHERE deleted_at IS NULL;
CREATE INDEX idx_models_graph_id ON models(graph_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_models_is_published ON models(is_published) WHERE deleted_at IS NULL;
CREATE INDEX idx_models_created_by ON models(created_by);
CREATE INDEX idx_models_created_at ON models(created_at DESC);
CREATE INDEX idx_models_updated_at ON models(updated_at DESC);
CREATE INDEX idx_models_deleted_at ON models(deleted_at) WHERE deleted_at IS NOT NULL;

-- Full-text search index
CREATE INDEX idx_models_fulltext ON models 
    USING gin(to_tsvector('english', 
        COALESCE(name, '') || ' ' || 
        COALESCE(description, '')
    )) WHERE deleted_at IS NULL;

-- Indexes for model_statistics table
CREATE INDEX idx_model_statistics_model_id ON model_statistics(model_id);
CREATE INDEX idx_model_statistics_validation_status ON model_statistics(validation_status);
CREATE INDEX idx_model_statistics_last_validation_at ON model_statistics(last_validation_at DESC);
CREATE INDEX idx_model_statistics_complexity_score ON model_statistics(complexity_score DESC NULLS LAST);

-- Indexes for model_tags table
CREATE INDEX idx_model_tags_model_id ON model_tags(model_id);
CREATE INDEX idx_model_tags_tag ON model_tags(tag);

-- Trigger to update updated_at timestamp
CREATE TRIGGER update_models_updated_at
    BEFORE UPDATE ON models
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_model_statistics_updated_at
    BEFORE UPDATE ON model_statistics
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger to create model_statistics entry when model is created
CREATE OR REPLACE FUNCTION create_model_statistics()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO model_statistics (model_id, last_modified_by)
    VALUES (NEW.id, NEW.created_by);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER model_create_statistics
    AFTER INSERT ON models
    FOR EACH ROW
    EXECUTE FUNCTION create_model_statistics();

-- Trigger to update model statistics when model is updated
CREATE OR REPLACE FUNCTION update_model_statistics_on_change()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE model_statistics
    SET 
        last_modified_by = NEW.updated_by,
        updated_at = NOW()
    WHERE model_id = NEW.id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER model_update_statistics
    AFTER UPDATE ON models
    FOR EACH ROW
    WHEN (OLD.updated_at IS DISTINCT FROM NEW.updated_at)
    EXECUTE FUNCTION update_model_statistics_on_change();

-- Function to increment diagram count
CREATE OR REPLACE FUNCTION increment_model_diagram_count(p_model_id UUID)
RETURNS VOID AS $$
BEGIN
    UPDATE model_statistics
    SET 
        total_diagrams = total_diagrams + 1,
        updated_at = NOW()
    WHERE model_id = p_model_id;
END;
$$ LANGUAGE plpgsql;

-- Function to decrement diagram count
CREATE OR REPLACE FUNCTION decrement_model_diagram_count(p_model_id UUID)
RETURNS VOID AS $$
BEGIN
    UPDATE model_statistics
    SET 
        total_diagrams = GREATEST(total_diagrams - 1, 0),
        updated_at = NOW()
    WHERE model_id = p_model_id;
END;
$$ LANGUAGE plpgsql;

-- Function to update model validation status
CREATE OR REPLACE FUNCTION update_model_validation_status(
    p_model_id UUID,
    p_status VARCHAR(20),
    p_errors INTEGER DEFAULT 0,
    p_warnings INTEGER DEFAULT 0
)
RETURNS VOID AS $$
BEGIN
    UPDATE model_statistics
    SET 
        validation_status = p_status,
        validation_errors = p_errors,
        validation_warnings = p_warnings,
        last_validation_at = NOW(),
        updated_at = NOW()
    WHERE model_id = p_model_id;
END;
$$ LANGUAGE plpgsql;

-- Function to calculate model complexity score
CREATE OR REPLACE FUNCTION calculate_model_complexity(p_model_id UUID)
RETURNS NUMERIC AS $$
DECLARE
    v_complexity NUMERIC;
    v_concepts INTEGER;
    v_relationships INTEGER;
    v_diagrams INTEGER;
BEGIN
    SELECT 
        total_concepts,
        total_relationships,
        total_diagrams
    INTO 
        v_concepts,
        v_relationships,
        v_diagrams
    FROM model_statistics
    WHERE model_id = p_model_id;
    
    -- Simple complexity formula (can be enhanced)
    v_complexity := (
        (v_concepts * 1.0) +
        (v_relationships * 1.5) +
        (v_diagrams * 0.5)
    );
    
    -- Update the score
    UPDATE model_statistics
    SET 
        complexity_score = v_complexity,
        updated_at = NOW()
    WHERE model_id = p_model_id;
    
    RETURN v_complexity;
END;
$$ LANGUAGE plpgsql;

-- Function to get model summary
CREATE OR REPLACE FUNCTION get_model_summary(p_model_id UUID)
RETURNS TABLE (
    model_id UUID,
    model_name VARCHAR(255),
    model_type VARCHAR(50),
    total_concepts INTEGER,
    total_relationships INTEGER,
    total_diagrams INTEGER,
    validation_status VARCHAR(20),
    complexity_score NUMERIC(5,2),
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        m.id,
        m.name,
        m.model_type,
        ms.total_concepts,
        ms.total_relationships,
        ms.total_diagrams,
        ms.validation_status,
        ms.complexity_score,
        m.created_at,
        m.updated_at
    FROM models m
    LEFT JOIN model_statistics ms ON ms.model_id = m.id
    WHERE m.id = p_model_id
    AND m.deleted_at IS NULL;
END;
$$ LANGUAGE plpgsql STABLE;

-- Logging
DO $$
BEGIN
    RAISE NOTICE 'Models schema created successfully';
END $$;