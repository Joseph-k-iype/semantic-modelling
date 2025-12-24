-- Model types enum
CREATE TYPE model_type AS ENUM ('er', 'uml_class', 'uml_sequence', 'uml_activity', 
                                 'uml_state', 'uml_component', 'uml_deployment', 
                                 'uml_package', 'bpmn', 'custom');

-- Model status enum
CREATE TYPE model_status AS ENUM ('draft', 'review', 'approved', 'published', 'archived');

-- Models table - metadata for semantic models
CREATE TABLE IF NOT EXISTS models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    folder_id UUID REFERENCES folders(id) ON DELETE SET NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    type model_type NOT NULL,
    status model_status NOT NULL DEFAULT 'draft',
    
    -- Graph reference
    graph_model_id VARCHAR(255) UNIQUE NOT NULL,
    
    -- Metadata
    tags TEXT[] DEFAULT ARRAY[]::TEXT[],
    metadata JSONB DEFAULT '{}'::JSONB,
    
    -- Ownership and tracking
    created_by UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    updated_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    -- Versioning
    current_version INT DEFAULT 1 NOT NULL,
    
    -- Publishing
    published_at TIMESTAMP WITH TIME ZONE,
    published_by UUID REFERENCES users(id) ON DELETE SET NULL,
    
    CONSTRAINT unique_model_name_per_workspace UNIQUE (workspace_id, name),
    CONSTRAINT valid_version CHECK (current_version > 0)
);

-- Model statistics (denormalized for performance)
CREATE TABLE IF NOT EXISTS model_statistics (
    model_id UUID PRIMARY KEY REFERENCES models(id) ON DELETE CASCADE,
    concept_count INT DEFAULT 0,
    relationship_count INT DEFAULT 0,
    diagram_count INT DEFAULT 0,
    version_count INT DEFAULT 1,
    last_edited_at TIMESTAMP WITH TIME ZONE,
    last_edited_by UUID REFERENCES users(id) ON DELETE SET NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Model tags table for efficient tag queries
CREATE TABLE IF NOT EXISTS model_tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id UUID NOT NULL REFERENCES models(id) ON DELETE CASCADE,
    tag VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    CONSTRAINT unique_model_tag UNIQUE (model_id, tag)
);

-- Model favorites
CREATE TABLE IF NOT EXISTS model_favorites (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id UUID NOT NULL REFERENCES models(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    CONSTRAINT unique_favorite UNIQUE (model_id, user_id)
);

-- Model shares (external sharing)
CREATE TABLE IF NOT EXISTS model_shares (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id UUID NOT NULL REFERENCES models(id) ON DELETE CASCADE,
    share_token VARCHAR(255) UNIQUE NOT NULL,
    created_by UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    permissions VARCHAR(50) NOT NULL DEFAULT 'view', -- view, comment, edit
    password_hash VARCHAR(255),
    expires_at TIMESTAMP WITH TIME ZONE,
    max_views INT,
    view_count INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    last_accessed_at TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT valid_share_permissions CHECK (permissions IN ('view', 'comment', 'edit'))
);

-- Indexes
CREATE INDEX idx_models_workspace_id ON models(workspace_id);
CREATE INDEX idx_models_folder_id ON models(folder_id);
CREATE INDEX idx_models_type ON models(type);
CREATE INDEX idx_models_status ON models(status);
CREATE INDEX idx_models_created_by ON models(created_by);
CREATE INDEX idx_models_created_at ON models(created_at);
CREATE INDEX idx_models_updated_at ON models(updated_at);
CREATE INDEX idx_models_graph_model_id ON models(graph_model_id);
CREATE INDEX idx_models_name_search ON models USING gin(to_tsvector('english', name));
CREATE INDEX idx_models_description_search ON models USING gin(to_tsvector('english', description));
CREATE INDEX idx_models_tags ON models USING gin(tags);

CREATE INDEX idx_model_statistics_last_edited_at ON model_statistics(last_edited_at);

CREATE INDEX idx_model_tags_tag ON model_tags(tag);
CREATE INDEX idx_model_tags_model_id ON model_tags(model_id);

CREATE INDEX idx_model_favorites_user_id ON model_favorites(user_id);
CREATE INDEX idx_model_favorites_model_id ON model_favorites(model_id);

CREATE INDEX idx_model_shares_token ON model_shares(share_token);
CREATE INDEX idx_model_shares_model_id ON model_shares(model_id);
CREATE INDEX idx_model_shares_expires_at ON model_shares(expires_at);
CREATE INDEX idx_model_shares_is_active ON model_shares(is_active);

-- Triggers
CREATE TRIGGER update_models_updated_at
    BEFORE UPDATE ON models
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_model_statistics_updated_at
    BEFORE UPDATE ON model_statistics
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Function to automatically create model statistics
CREATE OR REPLACE FUNCTION create_model_statistics()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO model_statistics (model_id, last_edited_at, last_edited_by)
    VALUES (NEW.id, NEW.created_at, NEW.created_by);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER create_model_stats
    AFTER INSERT ON models
    FOR EACH ROW
    EXECUTE FUNCTION create_model_statistics();

-- Function to sync tags to model_tags table
CREATE OR REPLACE FUNCTION sync_model_tags()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.tags IS NOT NULL THEN
        -- Delete old tags
        DELETE FROM model_tags WHERE model_id = NEW.id;
        
        -- Insert new tags
        INSERT INTO model_tags (model_id, tag)
        SELECT NEW.id, unnest(NEW.tags);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER sync_tags
    AFTER INSERT OR UPDATE OF tags ON models
    FOR EACH ROW
    EXECUTE FUNCTION sync_model_tags();

-- View for model list with statistics
CREATE OR REPLACE VIEW models_with_stats AS
SELECT 
    m.id,
    m.workspace_id,
    m.folder_id,
    m.name,
    m.description,
    m.type,
    m.status,
    m.tags,
    m.created_by,
    m.updated_by,
    m.created_at,
    m.updated_at,
    m.current_version,
    m.published_at,
    m.published_by,
    ms.concept_count,
    ms.relationship_count,
    ms.diagram_count,
    ms.version_count,
    ms.last_edited_at,
    ms.last_edited_by,
    u_created.full_name as created_by_name,
    u_created.email as created_by_email,
    u_updated.full_name as updated_by_name,
    u_updated.email as updated_by_email
FROM models m
LEFT JOIN model_statistics ms ON m.id = ms.model_id
LEFT JOIN users u_created ON m.created_by = u_created.id
LEFT JOIN users u_updated ON m.updated_by = u_updated.id;

-- Comments
COMMENT ON TABLE models IS 'Semantic model metadata - diagrams are projections of these models';
COMMENT ON TABLE model_statistics IS 'Denormalized statistics for model performance';
COMMENT ON TABLE model_tags IS 'Normalized tag storage for efficient querying';
COMMENT ON TABLE model_favorites IS 'User favorite models for quick access';
COMMENT ON TABLE model_shares IS 'External sharing links for models';

COMMENT ON COLUMN models.graph_model_id IS 'Reference ID to the model in FalkorDB graph database';
COMMENT ON COLUMN models.status IS 'Model lifecycle status: draft -> review -> approved -> published';
COMMENT ON COLUMN model_shares.share_token IS 'Unique token for sharing model externally';