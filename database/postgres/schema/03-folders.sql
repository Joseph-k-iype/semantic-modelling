-- Folders table for hierarchical organization
CREATE TABLE IF NOT EXISTS folders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    parent_id UUID REFERENCES folders(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    color VARCHAR(7), -- Hex color code
    icon VARCHAR(50),
    
    -- Materialized path for efficient queries
    path TEXT NOT NULL,
    depth INT NOT NULL DEFAULT 0,
    
    -- Ordering
    position INT DEFAULT 0,
    
    -- Metadata
    created_by UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    updated_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    CONSTRAINT unique_folder_name_per_parent UNIQUE (workspace_id, parent_id, name),
    CONSTRAINT valid_depth CHECK (depth >= 0),
    CONSTRAINT no_self_reference CHECK (id != parent_id)
);

-- Indexes
CREATE INDEX idx_folders_workspace_id ON folders(workspace_id);
CREATE INDEX idx_folders_parent_id ON folders(parent_id);
CREATE INDEX idx_folders_path ON folders(path);
CREATE INDEX idx_folders_created_by ON folders(created_by);
CREATE INDEX idx_folders_name_search ON folders USING gin(to_tsvector('english', name));

-- Trigger
CREATE TRIGGER update_folders_updated_at
    BEFORE UPDATE ON folders
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Function to update materialized path
CREATE OR REPLACE FUNCTION update_folder_path()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.parent_id IS NULL THEN
        NEW.path := NEW.id::text;
        NEW.depth := 0;
    ELSE
        SELECT path || '.' || NEW.id::text, depth + 1
        INTO NEW.path, NEW.depth
        FROM folders
        WHERE id = NEW.parent_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_folder_path
    BEFORE INSERT OR UPDATE OF parent_id ON folders
    FOR EACH ROW
    EXECUTE FUNCTION update_folder_path();

-- Function to prevent circular references
CREATE OR REPLACE FUNCTION check_folder_circular_reference()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.parent_id IS NOT NULL THEN
        IF EXISTS (
            SELECT 1 FROM folders
            WHERE id = NEW.parent_id
            AND path LIKE NEW.path || '.%'
        ) THEN
            RAISE EXCEPTION 'Circular reference detected in folder hierarchy';
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER check_circular_reference
    BEFORE UPDATE OF parent_id ON folders
    FOR EACH ROW
    WHEN (NEW.parent_id IS NOT NULL)
    EXECUTE FUNCTION check_folder_circular_reference();

-- View for folder tree with model counts
CREATE OR REPLACE VIEW folders_with_counts AS
SELECT 
    f.id,
    f.workspace_id,
    f.parent_id,
    f.name,
    f.description,
    f.path,
    f.depth,
    f.position,
    f.created_at,
    f.updated_at,
    COUNT(m.id) as model_count,
    u.full_name as created_by_name
FROM folders f
LEFT JOIN models m ON f.id = m.folder_id
LEFT JOIN users u ON f.created_by = u.id
GROUP BY f.id, u.id;

COMMENT ON TABLE folders IS 'Hierarchical folder structure for organizing models';
COMMENT ON COLUMN folders.path IS 'Materialized path for efficient tree queries (e.g., uuid1.uuid2.uuid3)';
COMMENT ON COLUMN folders.depth IS 'Depth in folder tree (0 = root)';