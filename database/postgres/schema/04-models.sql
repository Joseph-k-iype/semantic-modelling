-- database/postgres/schema/04-models.sql
-- Models table - Semantic models representing business concepts

-- Model types enum
CREATE TYPE model_type AS ENUM ('ER', 'UML', 'BPMN', 'CUSTOM');

-- Model status enum
CREATE TYPE model_status AS ENUM ('draft', 'in_review', 'published', 'archived');

CREATE TABLE IF NOT EXISTS models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    folder_id UUID REFERENCES folders(id) ON DELETE SET NULL,
    
    -- Model details
    name VARCHAR(255) NOT NULL,
    description TEXT,
    type model_type NOT NULL DEFAULT 'ER',
    
    -- Status and versioning
    status model_status DEFAULT 'draft' NOT NULL,
    version INT DEFAULT 1 NOT NULL,
    
    -- Tags for categorization
    tags TEXT[] DEFAULT ARRAY[]::TEXT[],
    
    -- Metadata
    metadata JSONB DEFAULT '{}'::JSONB,
    
    -- Ownership and audit
    created_by UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    updated_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    last_edited_by UUID REFERENCES users(id) ON DELETE SET NULL,
    last_edited_at TIMESTAMP WITH TIME ZONE,
    
    -- Publishing info
    published_at TIMESTAMP WITH TIME ZONE,
    published_by UUID REFERENCES users(id) ON DELETE SET NULL,
    
    -- Constraints
    CONSTRAINT unique_model_name_in_workspace UNIQUE (workspace_id, name),
    CONSTRAINT model_name_length CHECK (char_length(name) >= 1 AND char_length(name) <= 255),
    CONSTRAINT valid_version CHECK (version > 0)
);

-- Model tags table for efficient tag queries
CREATE TABLE IF NOT EXISTS model_tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id UUID NOT NULL REFERENCES models(id) ON DELETE CASCADE,
    tag VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    CONSTRAINT unique_model_tag UNIQUE (model_id, tag),
    CONSTRAINT tag_length CHECK (char_length(tag) >= 1 AND char_length(tag) <= 100)
);

-- Model favorites (user-specific)
CREATE TABLE IF NOT EXISTS model_favorites (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id UUID NOT NULL REFERENCES models(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    CONSTRAINT unique_favorite UNIQUE (model_id, user_id)
);

-- Model shares (external sharing with tokens)
CREATE TABLE IF NOT EXISTS model_shares (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id UUID NOT NULL REFERENCES models(id) ON DELETE CASCADE,
    share_token VARCHAR(255) UNIQUE NOT NULL,
    
    -- Share creator
    created_by UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Permissions
    permissions VARCHAR(50) NOT NULL DEFAULT 'view',
    password_hash VARCHAR(255),
    
    -- Limits
    expires_at TIMESTAMP WITH TIME ZONE,
    max_views INT,
    view_count INT DEFAULT 0,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    
    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    last_accessed_at TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT valid_share_permissions CHECK (permissions IN ('view', 'comment', 'edit')),
    CONSTRAINT valid_view_count CHECK (view_count >= 0),
    CONSTRAINT valid_max_views CHECK (max_views IS NULL OR max_views > 0)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_models_workspace_id ON models(workspace_id);
CREATE INDEX IF NOT EXISTS idx_models_folder_id ON models(folder_id);
CREATE INDEX IF NOT EXISTS idx_models_type ON models(type);
CREATE INDEX IF NOT EXISTS idx_models_status ON models(status);
CREATE INDEX IF NOT EXISTS idx_models_created_by ON models(created_by);
CREATE INDEX IF NOT EXISTS idx_models_created_at ON models(created_at);
CREATE INDEX IF NOT EXISTS idx_models_updated_at ON models(updated_at);
CREATE INDEX IF NOT EXISTS idx_models_tags ON models USING gin(tags);

CREATE INDEX IF NOT EXISTS idx_model_tags_model_id ON model_tags(model_id);
CREATE INDEX IF NOT EXISTS idx_model_tags_tag ON model_tags(tag);

CREATE INDEX IF NOT EXISTS idx_model_favorites_user_id ON model_favorites(user_id);
CREATE INDEX IF NOT EXISTS idx_model_favorites_model_id ON model_favorites(model_id);

CREATE INDEX IF NOT EXISTS idx_model_shares_token ON model_shares(share_token);
CREATE INDEX IF NOT EXISTS idx_model_shares_model_id ON model_shares(model_id);
CREATE INDEX IF NOT EXISTS idx_model_shares_is_active ON model_shares(is_active);

-- Trigger for updated_at
CREATE TRIGGER update_models_updated_at
    BEFORE UPDATE ON models
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Function to auto-update last_edited info
CREATE OR REPLACE FUNCTION update_model_last_edited()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.updated_by IS NOT NULL THEN
        NEW.last_edited_by = NEW.updated_by;
        NEW.last_edited_at = CURRENT_TIMESTAMP;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update last_edited
CREATE TRIGGER update_model_last_edited_trigger
    BEFORE UPDATE ON models
    FOR EACH ROW
    EXECUTE FUNCTION update_model_last_edited();

-- Comments
COMMENT ON TABLE models IS 'Semantic models representing business concepts';
COMMENT ON COLUMN models.type IS 'Model type: ER, UML, BPMN, or CUSTOM';
COMMENT ON COLUMN models.status IS 'Model lifecycle status';
COMMENT ON COLUMN models.tags IS 'Array of tags for categorization';
COMMENT ON COLUMN models.metadata IS 'Additional model metadata (JSON)';
COMMENT ON TABLE model_shares IS 'External sharing links with token-based access';