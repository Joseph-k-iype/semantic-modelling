-- database/postgres/schema/03-folders.sql
-- Folders table for organizing models within workspaces

-- Drop existing tables if exist (for clean reinstall)
DROP TABLE IF EXISTS folders CASCADE;

-- Folders table (hierarchical structure using materialized path)
CREATE TABLE folders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    parent_id UUID REFERENCES folders(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    path TEXT NOT NULL,
    level INTEGER NOT NULL DEFAULT 0,
    icon VARCHAR(50),
    color VARCHAR(7),
    settings JSONB DEFAULT '{}'::JSONB,
    metadata JSONB DEFAULT '{}'::JSONB,
    deleted_at TIMESTAMP WITH TIME ZONE,
    created_by UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    updated_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    
    -- Constraints
    CONSTRAINT folders_name_check CHECK (LENGTH(TRIM(name)) >= 1 AND LENGTH(name) <= 255),
    CONSTRAINT folders_color_check CHECK (color IS NULL OR color ~* '^#[0-9A-Fa-f]{6}$'),
    CONSTRAINT folders_level_check CHECK (level >= 0 AND level < 10),
    CONSTRAINT folders_path_check CHECK (LENGTH(path) >= 1),
    CONSTRAINT folders_parent_workspace_check CHECK (
        parent_id IS NULL OR 
        workspace_id = (SELECT workspace_id FROM folders WHERE id = parent_id)
    ),
    -- Ensure unique name within same parent
    CONSTRAINT folders_unique_name_per_parent UNIQUE(workspace_id, parent_id, name, deleted_at)
);

-- Indexes for folders table
CREATE INDEX idx_folders_workspace_id ON folders(workspace_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_folders_parent_id ON folders(parent_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_folders_path ON folders USING btree(path text_pattern_ops) WHERE deleted_at IS NULL;
CREATE INDEX idx_folders_level ON folders(level) WHERE deleted_at IS NULL;
CREATE INDEX idx_folders_created_by ON folders(created_by);
CREATE INDEX idx_folders_created_at ON folders(created_at DESC);
CREATE INDEX idx_folders_deleted_at ON folders(deleted_at) WHERE deleted_at IS NOT NULL;

-- Full-text search index
CREATE INDEX idx_folders_fulltext ON folders 
    USING gin(to_tsvector('english', 
        COALESCE(name, '') || ' ' || 
        COALESCE(description, '')
    )) WHERE deleted_at IS NULL;

-- Trigger to update updated_at timestamp
CREATE TRIGGER update_folders_updated_at
    BEFORE UPDATE ON folders
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger to manage folder path and level
CREATE OR REPLACE FUNCTION manage_folder_path()
RETURNS TRIGGER AS $$
DECLARE
    parent_path TEXT;
    parent_level INTEGER;
BEGIN
    -- For root folders (no parent)
    IF NEW.parent_id IS NULL THEN
        NEW.path = NEW.id::TEXT;
        NEW.level = 0;
    ELSE
        -- Get parent's path and level
        SELECT path, level INTO parent_path, parent_level
        FROM folders
        WHERE id = NEW.parent_id;
        
        -- Check if parent exists
        IF parent_path IS NULL THEN
            RAISE EXCEPTION 'Parent folder does not exist';
        END IF;
        
        -- Build new path and level
        NEW.path = parent_path || '/' || NEW.id::TEXT;
        NEW.level = parent_level + 1;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER folder_manage_path
    BEFORE INSERT OR UPDATE OF parent_id ON folders
    FOR EACH ROW
    EXECUTE FUNCTION manage_folder_path();

-- Trigger to prevent circular references
CREATE OR REPLACE FUNCTION prevent_folder_circular_reference()
RETURNS TRIGGER AS $$
BEGIN
    -- Check if new parent is a descendant of current folder
    IF NEW.parent_id IS NOT NULL AND EXISTS (
        SELECT 1 FROM folders
        WHERE id = NEW.parent_id
        AND path LIKE NEW.path || '%'
    ) THEN
        RAISE EXCEPTION 'Cannot move folder into its own descendant';
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER folder_prevent_circular_reference
    BEFORE UPDATE OF parent_id ON folders
    FOR EACH ROW
    WHEN (OLD.parent_id IS DISTINCT FROM NEW.parent_id)
    EXECUTE FUNCTION prevent_folder_circular_reference();

-- Trigger to update paths of descendants when folder is moved
CREATE OR REPLACE FUNCTION update_descendant_paths()
RETURNS TRIGGER AS $$
BEGIN
    -- Only update if parent has changed
    IF OLD.parent_id IS DISTINCT FROM NEW.parent_id THEN
        -- Update all descendants' paths
        UPDATE folders
        SET 
            path = REPLACE(path, OLD.path, NEW.path),
            level = level + (NEW.level - OLD.level)
        WHERE path LIKE OLD.path || '/%';
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER folder_update_descendant_paths
    AFTER UPDATE OF parent_id ON folders
    FOR EACH ROW
    WHEN (OLD.parent_id IS DISTINCT FROM NEW.parent_id)
    EXECUTE FUNCTION update_descendant_paths();

-- Function to get folder breadcrumbs
CREATE OR REPLACE FUNCTION get_folder_breadcrumbs(folder_id UUID)
RETURNS TABLE (
    id UUID,
    name VARCHAR(255),
    level INTEGER
) AS $$
BEGIN
    RETURN QUERY
    WITH RECURSIVE breadcrumbs AS (
        -- Base case: start with the given folder
        SELECT f.id, f.name, f.level, f.parent_id
        FROM folders f
        WHERE f.id = folder_id
        
        UNION ALL
        
        -- Recursive case: get parent folders
        SELECT f.id, f.name, f.level, f.parent_id
        FROM folders f
        INNER JOIN breadcrumbs b ON f.id = b.parent_id
    )
    SELECT b.id, b.name, b.level
    FROM breadcrumbs b
    ORDER BY b.level ASC;
END;
$$ LANGUAGE plpgsql STABLE;

-- Function to get folder tree (children)
CREATE OR REPLACE FUNCTION get_folder_tree(root_folder_id UUID DEFAULT NULL, max_depth INTEGER DEFAULT 10)
RETURNS TABLE (
    id UUID,
    parent_id UUID,
    name VARCHAR(255),
    level INTEGER,
    path TEXT,
    has_children BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    WITH RECURSIVE folder_tree AS (
        -- Base case: start with root or specified folder
        SELECT 
            f.id,
            f.parent_id,
            f.name,
            f.level,
            f.path,
            EXISTS(SELECT 1 FROM folders c WHERE c.parent_id = f.id AND c.deleted_at IS NULL) as has_children
        FROM folders f
        WHERE (root_folder_id IS NULL AND f.parent_id IS NULL) 
           OR (f.id = root_folder_id)
           AND f.deleted_at IS NULL
        
        UNION ALL
        
        -- Recursive case: get children
        SELECT 
            f.id,
            f.parent_id,
            f.name,
            f.level,
            f.path,
            EXISTS(SELECT 1 FROM folders c WHERE c.parent_id = f.id AND c.deleted_at IS NULL) as has_children
        FROM folders f
        INNER JOIN folder_tree ft ON f.parent_id = ft.id
        WHERE f.deleted_at IS NULL
        AND f.level <= max_depth
    )
    SELECT * FROM folder_tree
    ORDER BY level, name;
END;
$$ LANGUAGE plpgsql STABLE;

-- Function to move folder to new parent
CREATE OR REPLACE FUNCTION move_folder(
    p_folder_id UUID,
    p_new_parent_id UUID,
    p_user_id UUID
)
RETURNS BOOLEAN AS $$
DECLARE
    v_workspace_id UUID;
    v_new_parent_workspace UUID;
BEGIN
    -- Get folder's workspace
    SELECT workspace_id INTO v_workspace_id
    FROM folders
    WHERE id = p_folder_id;
    
    -- If new parent specified, check it's in same workspace
    IF p_new_parent_id IS NOT NULL THEN
        SELECT workspace_id INTO v_new_parent_workspace
        FROM folders
        WHERE id = p_new_parent_id;
        
        IF v_workspace_id != v_new_parent_workspace THEN
            RAISE EXCEPTION 'Cannot move folder to different workspace';
        END IF;
    END IF;
    
    -- Update folder
    UPDATE folders
    SET parent_id = p_new_parent_id,
        updated_by = p_user_id,
        updated_at = NOW()
    WHERE id = p_folder_id;
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- Logging
DO $$
BEGIN
    RAISE NOTICE 'Folders schema created successfully';
END $$;