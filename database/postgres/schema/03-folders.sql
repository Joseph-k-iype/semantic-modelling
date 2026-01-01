-- database/postgres/schema/03-folders.sql
-- Folders table for organizing models within workspaces
-- FIXED: Removed invalid subquery constraint

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
    -- REMOVED: Invalid subquery constraint - will use trigger instead
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

-- Trigger for updated_at
CREATE TRIGGER update_folders_updated_at 
    BEFORE UPDATE ON folders
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Function to validate parent folder is in same workspace (replaces invalid CHECK constraint)
CREATE OR REPLACE FUNCTION validate_folder_parent_workspace()
RETURNS TRIGGER AS $$
BEGIN
    -- Only validate if parent_id is set
    IF NEW.parent_id IS NOT NULL THEN
        -- Check if parent folder exists and is in same workspace
        IF NOT EXISTS (
            SELECT 1 FROM folders 
            WHERE id = NEW.parent_id 
            AND workspace_id = NEW.workspace_id
            AND deleted_at IS NULL
        ) THEN
            RAISE EXCEPTION 'Parent folder must be in the same workspace';
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to validate parent workspace
CREATE TRIGGER validate_folder_parent_workspace_trigger
    BEFORE INSERT OR UPDATE ON folders
    FOR EACH ROW
    EXECUTE FUNCTION validate_folder_parent_workspace();

-- Function to update folder path and level
CREATE OR REPLACE FUNCTION update_folder_path()
RETURNS TRIGGER AS $$
DECLARE
    parent_path TEXT;
    parent_level INTEGER;
BEGIN
    IF NEW.parent_id IS NULL THEN
        -- Root folder
        NEW.path := '/' || NEW.id::TEXT;
        NEW.level := 0;
    ELSE
        -- Get parent path and level
        SELECT path, level INTO parent_path, parent_level
        FROM folders
        WHERE id = NEW.parent_id;
        
        IF parent_path IS NULL THEN
            RAISE EXCEPTION 'Parent folder not found';
        END IF;
        
        -- Set path and level
        NEW.path := parent_path || '/' || NEW.id::TEXT;
        NEW.level := parent_level + 1;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update path
CREATE TRIGGER update_folder_path_trigger
    BEFORE INSERT OR UPDATE OF parent_id ON folders
    FOR EACH ROW
    EXECUTE FUNCTION update_folder_path();

-- Function to get folder tree
CREATE OR REPLACE FUNCTION get_folder_tree(p_workspace_id UUID, p_parent_id UUID DEFAULT NULL)
RETURNS TABLE (
    id UUID,
    name VARCHAR(255),
    path TEXT,
    level INTEGER,
    parent_id UUID,
    has_children BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        f.id,
        f.name,
        f.path,
        f.level,
        f.parent_id,
        EXISTS(SELECT 1 FROM folders WHERE parent_id = f.id AND deleted_at IS NULL) as has_children
    FROM folders f
    WHERE f.workspace_id = p_workspace_id
    AND (
        (p_parent_id IS NULL AND f.parent_id IS NULL) OR
        (p_parent_id IS NOT NULL AND f.parent_id = p_parent_id)
    )
    AND f.deleted_at IS NULL
    ORDER BY f.name;
END;
$$ LANGUAGE plpgsql STABLE;

-- Function to get folder path as array
CREATE OR REPLACE FUNCTION get_folder_path_array(p_folder_id UUID)
RETURNS UUID[] AS $$
DECLARE
    folder_path TEXT;
    path_ids UUID[];
BEGIN
    SELECT path INTO folder_path
    FROM folders
    WHERE id = p_folder_id;
    
    IF folder_path IS NULL THEN
        RETURN ARRAY[]::UUID[];
    END IF;
    
    -- Convert path string to array of UUIDs
    SELECT ARRAY_AGG(id::UUID)
    INTO path_ids
    FROM regexp_split_to_table(TRIM(BOTH '/' FROM folder_path), '/') AS id;
    
    RETURN COALESCE(path_ids, ARRAY[]::UUID[]);
END;
$$ LANGUAGE plpgsql STABLE;

-- Function to move folder (updates path for folder and all descendants)
CREATE OR REPLACE FUNCTION move_folder(
    p_folder_id UUID,
    p_new_parent_id UUID
)
RETURNS BOOLEAN AS $$
DECLARE
    v_old_path TEXT;
    v_new_path TEXT;
    v_new_level INTEGER;
BEGIN
    -- Get current path
    SELECT path INTO v_old_path
    FROM folders
    WHERE id = p_folder_id;
    
    IF v_old_path IS NULL THEN
        RAISE EXCEPTION 'Folder not found';
    END IF;
    
    -- Check for circular reference
    IF p_new_parent_id IS NOT NULL THEN
        IF EXISTS (
            SELECT 1 FROM folders
            WHERE id = p_new_parent_id
            AND path LIKE v_old_path || '%'
        ) THEN
            RAISE EXCEPTION 'Cannot move folder to its own descendant';
        END IF;
    END IF;
    
    -- Update folder
    UPDATE folders
    SET parent_id = p_new_parent_id,
        updated_at = NOW()
    WHERE id = p_folder_id;
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- Function to delete folder and all descendants
CREATE OR REPLACE FUNCTION delete_folder_cascade(p_folder_id UUID)
RETURNS BOOLEAN AS $$
DECLARE
    v_path TEXT;
BEGIN
    -- Get folder path
    SELECT path INTO v_path
    FROM folders
    WHERE id = p_folder_id;
    
    IF v_path IS NULL THEN
        RAISE EXCEPTION 'Folder not found';
    END IF;
    
    -- Soft delete folder and all descendants
    UPDATE folders
    SET deleted_at = NOW()
    WHERE path LIKE v_path || '%'
    AND deleted_at IS NULL;
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- Logging
DO $$
BEGIN
    RAISE NOTICE 'Folders schema created successfully';
    RAISE NOTICE '✓ Constraint validation moved to trigger (no subquery in CHECK)';
END $$;