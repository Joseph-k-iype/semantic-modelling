-- database/postgres/schema/03-folders.sql
-- Folders table - Hierarchical organization within workspaces

CREATE TABLE IF NOT EXISTS folders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    parent_id UUID REFERENCES folders(id) ON DELETE CASCADE,
    
    -- Folder details
    name VARCHAR(255) NOT NULL,
    description TEXT,
    color VARCHAR(50),
    icon VARCHAR(100),
    
    -- Path for efficient queries (materialized path)
    path TEXT NOT NULL,
    
    -- Position for ordering
    position INT DEFAULT 0 NOT NULL,
    
    -- Ownership
    created_by UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    -- Constraints
    CONSTRAINT unique_folder_name_in_parent UNIQUE (workspace_id, parent_id, name),
    CONSTRAINT folder_name_length CHECK (char_length(name) >= 1 AND char_length(name) <= 255),
    CONSTRAINT no_self_reference CHECK (id != parent_id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_folders_workspace_id ON folders(workspace_id);
CREATE INDEX IF NOT EXISTS idx_folders_parent_id ON folders(parent_id);
CREATE INDEX IF NOT EXISTS idx_folders_created_by ON folders(created_by);
CREATE INDEX IF NOT EXISTS idx_folders_path ON folders USING gin(path gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_folders_position ON folders(workspace_id, parent_id, position);

-- Trigger for updated_at
CREATE TRIGGER update_folders_updated_at
    BEFORE UPDATE ON folders
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Function to update folder path
CREATE OR REPLACE FUNCTION update_folder_path()
RETURNS TRIGGER AS $$
DECLARE
    parent_path TEXT;
BEGIN
    IF NEW.parent_id IS NULL THEN
        NEW.path = '/' || NEW.id::TEXT;
    ELSE
        SELECT path INTO parent_path FROM folders WHERE id = NEW.parent_id;
        NEW.path = parent_path || '/' || NEW.id::TEXT;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update path
CREATE TRIGGER update_folder_path_trigger
    BEFORE INSERT OR UPDATE ON folders
    FOR EACH ROW
    EXECUTE FUNCTION update_folder_path();

-- Function to prevent circular folder references
CREATE OR REPLACE FUNCTION check_folder_circular_reference()
RETURNS TRIGGER AS $$
DECLARE
    current_parent UUID;
    depth INT := 0;
    max_depth INT := 100;
BEGIN
    current_parent := NEW.parent_id;
    
    WHILE current_parent IS NOT NULL AND depth < max_depth LOOP
        IF current_parent = NEW.id THEN
            RAISE EXCEPTION 'Circular folder reference detected';
        END IF;
        
        SELECT parent_id INTO current_parent FROM folders WHERE id = current_parent;
        depth := depth + 1;
    END LOOP;
    
    IF depth >= max_depth THEN
        RAISE EXCEPTION 'Folder hierarchy too deep (max % levels)', max_depth;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to check circular references
CREATE TRIGGER check_folder_circular_reference_trigger
    BEFORE INSERT OR UPDATE ON folders
    FOR EACH ROW
    EXECUTE FUNCTION check_folder_circular_reference();

-- Comments
COMMENT ON TABLE folders IS 'Hierarchical folder structure for organizing models';
COMMENT ON COLUMN folders.path IS 'Materialized path for efficient hierarchy queries';
COMMENT ON COLUMN folders.position IS 'Sort order within parent folder';