-- database/postgres/schema/07-versions.sql
-- Versions table for model versioning and change tracking

-- Drop existing tables if exist (for clean reinstall)
DROP TABLE IF EXISTS version_changes CASCADE;
DROP TABLE IF EXISTS versions CASCADE;

-- Versions table
CREATE TABLE versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_id UUID NOT NULL REFERENCES models(id) ON DELETE CASCADE,
    version_number VARCHAR(20) NOT NULL,
    version_type version_type NOT NULL,
    major INTEGER NOT NULL DEFAULT 1,
    minor INTEGER NOT NULL DEFAULT 0,
    patch INTEGER NOT NULL DEFAULT 0,
    name VARCHAR(255),
    description TEXT,
    change_summary TEXT,
    snapshot_data JSONB NOT NULL,
    graph_snapshot_id VARCHAR(255),
    is_published BOOLEAN DEFAULT FALSE NOT NULL,
    published_at TIMESTAMP WITH TIME ZONE,
    tags JSONB DEFAULT '[]'::JSONB,
    metadata JSONB DEFAULT '{}'::JSONB,
    created_by UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    
    -- Constraints
    CONSTRAINT versions_version_number_check CHECK (version_number ~* '^\d+\.\d+\.\d+$'),
    CONSTRAINT versions_major_check CHECK (major >= 0),
    CONSTRAINT versions_minor_check CHECK (minor >= 0),
    CONSTRAINT versions_patch_check CHECK (patch >= 0),
    -- Ensure unique version number per model
    CONSTRAINT versions_unique_version UNIQUE(model_id, version_number)
);

-- Version changes table (detailed change log)
CREATE TABLE version_changes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    version_id UUID NOT NULL REFERENCES versions(id) ON DELETE CASCADE,
    change_type VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID NOT NULL,
    entity_name VARCHAR(255),
    old_value JSONB,
    new_value JSONB,
    change_description TEXT,
    metadata JSONB DEFAULT '{}'::JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    
    -- Constraints
    CONSTRAINT version_changes_change_type_check CHECK (change_type IN (
        'CREATE',
        'UPDATE',
        'DELETE',
        'RENAME',
        'MOVE',
        'PROPERTY_CHANGE'
    )),
    CONSTRAINT version_changes_entity_type_check CHECK (LENGTH(entity_type) >= 1)
);

-- Indexes for versions table
CREATE INDEX idx_versions_model_id ON versions(model_id);
CREATE INDEX idx_versions_version_number ON versions(version_number);
CREATE INDEX idx_versions_version_type ON versions(version_type);
CREATE INDEX idx_versions_is_published ON versions(is_published) WHERE is_published = TRUE;
CREATE INDEX idx_versions_created_by ON versions(created_by);
CREATE INDEX idx_versions_created_at ON versions(created_at DESC);
CREATE INDEX idx_versions_published_at ON versions(published_at DESC NULLS LAST);
CREATE INDEX idx_versions_major_minor_patch ON versions(major DESC, minor DESC, patch DESC);

-- Full-text search index
CREATE INDEX idx_versions_fulltext ON versions 
    USING gin(to_tsvector('english', 
        COALESCE(name, '') || ' ' || 
        COALESCE(description, '') || ' ' ||
        COALESCE(change_summary, '')
    ));

-- Indexes for version_changes table
CREATE INDEX idx_version_changes_version_id ON version_changes(version_id);
CREATE INDEX idx_version_changes_change_type ON version_changes(change_type);
CREATE INDEX idx_version_changes_entity_type ON version_changes(entity_type);
CREATE INDEX idx_version_changes_entity_id ON version_changes(entity_id);
CREATE INDEX idx_version_changes_created_at ON version_changes(created_at DESC);

-- Trigger to generate version number
CREATE OR REPLACE FUNCTION generate_version_number()
RETURNS TRIGGER AS $$
BEGIN
    NEW.version_number = generate_version_string(NEW.major, NEW.minor, NEW.patch);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER version_generate_number
    BEFORE INSERT OR UPDATE OF major, minor, patch ON versions
    FOR EACH ROW
    EXECUTE FUNCTION generate_version_number();

-- Trigger to update model_statistics version count
CREATE OR REPLACE FUNCTION update_version_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE model_statistics
        SET 
            total_versions = total_versions + 1,
            updated_at = NOW()
        WHERE model_id = NEW.model_id;
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE model_statistics
        SET 
            total_versions = GREATEST(total_versions - 1, 0),
            updated_at = NOW()
        WHERE model_id = OLD.model_id;
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER version_update_count_insert
    AFTER INSERT ON versions
    FOR EACH ROW
    EXECUTE FUNCTION update_version_count();

CREATE TRIGGER version_update_count_delete
    AFTER DELETE ON versions
    FOR EACH ROW
    EXECUTE FUNCTION update_version_count();

-- Function to get next version number
CREATE OR REPLACE FUNCTION get_next_version_number(
    p_model_id UUID,
    p_version_type version_type
)
RETURNS TABLE (
    major INTEGER,
    minor INTEGER,
    patch INTEGER,
    version_string VARCHAR(20)
) AS $$
DECLARE
    v_current_major INTEGER;
    v_current_minor INTEGER;
    v_current_patch INTEGER;
    v_next_major INTEGER;
    v_next_minor INTEGER;
    v_next_patch INTEGER;
BEGIN
    -- Get current latest version
    SELECT v.major, v.minor, v.patch
    INTO v_current_major, v_current_minor, v_current_patch
    FROM versions v
    WHERE v.model_id = p_model_id
    ORDER BY v.major DESC, v.minor DESC, v.patch DESC
    LIMIT 1;
    
    -- If no versions exist, start with 1.0.0
    IF v_current_major IS NULL THEN
        v_next_major := 1;
        v_next_minor := 0;
        v_next_patch := 0;
    ELSE
        -- Calculate next version based on type
        CASE p_version_type
            WHEN 'MAJOR' THEN
                v_next_major := v_current_major + 1;
                v_next_minor := 0;
                v_next_patch := 0;
            WHEN 'MINOR' THEN
                v_next_major := v_current_major;
                v_next_minor := v_current_minor + 1;
                v_next_patch := 0;
            WHEN 'PATCH' THEN
                v_next_major := v_current_major;
                v_next_minor := v_current_minor;
                v_next_patch := v_current_patch + 1;
        END CASE;
    END IF;
    
    RETURN QUERY SELECT 
        v_next_major,
        v_next_minor,
        v_next_patch,
        generate_version_string(v_next_major, v_next_minor, v_next_patch);
END;
$$ LANGUAGE plpgsql STABLE;

-- Function to create version snapshot
CREATE OR REPLACE FUNCTION create_version_snapshot(
    p_model_id UUID,
    p_version_type version_type,
    p_name VARCHAR(255),
    p_description TEXT,
    p_change_summary TEXT,
    p_snapshot_data JSONB,
    p_user_id UUID
)
RETURNS UUID AS $$
DECLARE
    v_version_id UUID;
    v_next_version RECORD;
BEGIN
    -- Get next version number
    SELECT * INTO v_next_version
    FROM get_next_version_number(p_model_id, p_version_type);
    
    -- Create version
    INSERT INTO versions (
        model_id,
        major,
        minor,
        patch,
        version_type,
        name,
        description,
        change_summary,
        snapshot_data,
        created_by
    ) VALUES (
        p_model_id,
        v_next_version.major,
        v_next_version.minor,
        v_next_version.patch,
        p_version_type,
        p_name,
        p_description,
        p_change_summary,
        p_snapshot_data,
        p_user_id
    )
    RETURNING id INTO v_version_id;
    
    RETURN v_version_id;
END;
$$ LANGUAGE plpgsql;

-- Function to get version history
CREATE OR REPLACE FUNCTION get_version_history(p_model_id UUID)
RETURNS TABLE (
    version_id UUID,
    version_number VARCHAR(20),
    version_type version_type,
    name VARCHAR(255),
    change_summary TEXT,
    is_published BOOLEAN,
    created_by_id UUID,
    created_by_name VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE,
    change_count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        v.id,
        v.version_number,
        v.version_type,
        v.name,
        v.change_summary,
        v.is_published,
        v.created_by,
        u.full_name,
        v.created_at,
        COUNT(vc.id) as change_count
    FROM versions v
    JOIN users u ON u.id = v.created_by
    LEFT JOIN version_changes vc ON vc.version_id = v.id
    WHERE v.model_id = p_model_id
    GROUP BY v.id, v.version_number, v.version_type, v.name, v.change_summary, 
             v.is_published, v.created_by, u.full_name, v.created_at
    ORDER BY v.major DESC, v.minor DESC, v.patch DESC;
END;
$$ LANGUAGE plpgsql STABLE;

-- Function to compare versions
CREATE OR REPLACE FUNCTION compare_versions(
    p_version_1_id UUID,
    p_version_2_id UUID
)
RETURNS TABLE (
    change_type VARCHAR(50),
    entity_type VARCHAR(50),
    entity_id UUID,
    entity_name VARCHAR(255),
    old_value JSONB,
    new_value JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        vc.change_type,
        vc.entity_type,
        vc.entity_id,
        vc.entity_name,
        vc.old_value,
        vc.new_value
    FROM version_changes vc
    WHERE vc.version_id IN (p_version_1_id, p_version_2_id)
    ORDER BY vc.created_at;
END;
$$ LANGUAGE plpgsql STABLE;

-- Function to rollback to version
CREATE OR REPLACE FUNCTION rollback_to_version(
    p_version_id UUID,
    p_user_id UUID
)
RETURNS UUID AS $$
DECLARE
    v_version RECORD;
    v_new_version_id UUID;
BEGIN
    -- Get version data
    SELECT * INTO v_version
    FROM versions
    WHERE id = p_version_id;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Version not found';
    END IF;
    
    -- Create new version with rollback data
    v_new_version_id := create_version_snapshot(
        v_version.model_id,
        'PATCH',
        'Rollback to ' || v_version.version_number,
        'Rolled back to version ' || v_version.version_number,
        'System rollback',
        v_version.snapshot_data,
        p_user_id
    );
    
    RETURN v_new_version_id;
END;
$$ LANGUAGE plpgsql;

-- Function to tag version
CREATE OR REPLACE FUNCTION tag_version(
    p_version_id UUID,
    p_tags TEXT[]
)
RETURNS VOID AS $$
BEGIN
    UPDATE versions
    SET 
        tags = to_jsonb(p_tags),
        updated_at = NOW()
    WHERE id = p_version_id;
END;
$$ LANGUAGE plpgsql;

-- Function to get versions by tag
CREATE OR REPLACE FUNCTION get_versions_by_tag(p_model_id UUID, p_tag TEXT)
RETURNS TABLE (
    version_id UUID,
    version_number VARCHAR(20),
    name VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        v.id,
        v.version_number,
        v.name,
        v.created_at
    FROM versions v
    WHERE v.model_id = p_model_id
    AND v.tags ? p_tag
    ORDER BY v.created_at DESC;
END;
$$ LANGUAGE plpgsql STABLE;

-- Logging
DO $$
BEGIN
    RAISE NOTICE 'Versions schema created successfully';
END $$;