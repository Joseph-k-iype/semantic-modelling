-- database/postgres/schema/06-layouts.sql
-- Layouts table for user-controlled diagram layouts

-- Drop existing tables if exist (for clean reinstall)
DROP TABLE IF EXISTS layout_snapshots CASCADE;
DROP TABLE IF EXISTS layouts CASCADE;

-- Layouts table (user-owned layout configurations)
CREATE TABLE layouts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    diagram_id UUID NOT NULL REFERENCES diagrams(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    layout_type layout_type NOT NULL,
    layout_data JSONB NOT NULL DEFAULT '{}'::JSONB,
    constraints JSONB DEFAULT '{}'::JSONB,
    settings JSONB DEFAULT '{}'::JSONB,
    is_active BOOLEAN DEFAULT FALSE NOT NULL,
    is_auto_apply BOOLEAN DEFAULT FALSE NOT NULL,
    deleted_at TIMESTAMP WITH TIME ZONE,
    created_by UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    updated_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    
    -- Constraints
    CONSTRAINT layouts_name_check CHECK (LENGTH(TRIM(name)) >= 1 AND LENGTH(name) <= 255),
    -- Ensure unique name within diagram
    CONSTRAINT layouts_unique_name UNIQUE(diagram_id, name, deleted_at)
);

-- Layout snapshots table (for layout history and rollback)
CREATE TABLE layout_snapshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    layout_id UUID NOT NULL REFERENCES layouts(id) ON DELETE CASCADE,
    snapshot_name VARCHAR(255),
    layout_data JSONB NOT NULL,
    metadata JSONB DEFAULT '{}'::JSONB,
    created_by UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    
    -- Constraints
    CONSTRAINT layout_snapshots_snapshot_name_check CHECK (
        snapshot_name IS NULL OR LENGTH(TRIM(snapshot_name)) >= 1
    )
);

-- Indexes for layouts table
CREATE INDEX idx_layouts_diagram_id ON layouts(diagram_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_layouts_layout_type ON layouts(layout_type) WHERE deleted_at IS NULL;
CREATE INDEX idx_layouts_is_active ON layouts(is_active) WHERE is_active = TRUE AND deleted_at IS NULL;
CREATE INDEX idx_layouts_is_auto_apply ON layouts(is_auto_apply) WHERE is_auto_apply = TRUE;
CREATE INDEX idx_layouts_created_by ON layouts(created_by);
CREATE INDEX idx_layouts_created_at ON layouts(created_at DESC);
CREATE INDEX idx_layouts_updated_at ON layouts(updated_at DESC);
CREATE INDEX idx_layouts_deleted_at ON layouts(deleted_at) WHERE deleted_at IS NOT NULL;

-- Full-text search index
CREATE INDEX idx_layouts_fulltext ON layouts 
    USING gin(to_tsvector('english', 
        COALESCE(name, '') || ' ' || 
        COALESCE(description, '')
    )) WHERE deleted_at IS NULL;

-- Indexes for layout_snapshots table
CREATE INDEX idx_layout_snapshots_layout_id ON layout_snapshots(layout_id);
CREATE INDEX idx_layout_snapshots_created_by ON layout_snapshots(created_by);
CREATE INDEX idx_layout_snapshots_created_at ON layout_snapshots(created_at DESC);

-- Trigger to update updated_at timestamp
CREATE TRIGGER update_layouts_updated_at
    BEFORE UPDATE ON layouts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger to ensure only one active layout per diagram
CREATE OR REPLACE FUNCTION ensure_single_active_layout()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.is_active = TRUE THEN
        -- Set all other layouts in the diagram to inactive
        UPDATE layouts
        SET is_active = FALSE
        WHERE diagram_id = NEW.diagram_id
        AND id != NEW.id
        AND is_active = TRUE;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER layout_ensure_single_active
    AFTER INSERT OR UPDATE OF is_active ON layouts
    FOR EACH ROW
    WHEN (NEW.is_active = TRUE)
    EXECUTE FUNCTION ensure_single_active_layout();

-- Trigger to create snapshot on significant layout changes
CREATE OR REPLACE FUNCTION create_layout_snapshot_on_change()
RETURNS TRIGGER AS $$
BEGIN
    -- Only create snapshot if layout_data has changed significantly
    IF TG_OP = 'UPDATE' AND OLD.layout_data IS DISTINCT FROM NEW.layout_data THEN
        INSERT INTO layout_snapshots (
            layout_id,
            snapshot_name,
            layout_data,
            metadata,
            created_by
        ) VALUES (
            NEW.id,
            'Auto-snapshot: ' || TO_CHAR(NOW(), 'YYYY-MM-DD HH24:MI:SS'),
            OLD.layout_data,
            jsonb_build_object(
                'trigger', 'auto',
                'previous_update', OLD.updated_at
            ),
            NEW.updated_by
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER layout_create_snapshot_on_change
    AFTER UPDATE OF layout_data ON layouts
    FOR EACH ROW
    EXECUTE FUNCTION create_layout_snapshot_on_change();

-- Trigger to set first layout as active
CREATE OR REPLACE FUNCTION set_first_layout_as_active()
RETURNS TRIGGER AS $$
DECLARE
    layout_count INTEGER;
BEGIN
    -- Count existing layouts for this diagram
    SELECT COUNT(*) INTO layout_count
    FROM layouts
    WHERE diagram_id = NEW.diagram_id
    AND deleted_at IS NULL;
    
    -- If this is the first layout, make it active
    IF layout_count = 1 THEN
        NEW.is_active = TRUE;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER layout_set_first_as_active
    BEFORE INSERT ON layouts
    FOR EACH ROW
    EXECUTE FUNCTION set_first_layout_as_active();

-- Function to apply layout to diagram elements
CREATE OR REPLACE FUNCTION apply_layout_to_diagram(p_layout_id UUID)
RETURNS VOID AS $$
DECLARE
    v_layout RECORD;
    v_element RECORD;
    v_position JSONB;
BEGIN
    -- Get layout data
    SELECT * INTO v_layout
    FROM layouts
    WHERE id = p_layout_id
    AND deleted_at IS NULL;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Layout not found';
    END IF;
    
    -- Apply positions to diagram elements
    FOR v_element IN 
        SELECT id, concept_id
        FROM diagram_elements
        WHERE diagram_id = v_layout.diagram_id
    LOOP
        -- Get position from layout_data
        v_position := v_layout.layout_data -> v_element.concept_id::TEXT;
        
        IF v_position IS NOT NULL THEN
            UPDATE diagram_elements
            SET 
                position_x = (v_position->>'x')::NUMERIC,
                position_y = (v_position->>'y')::NUMERIC,
                width = (v_position->>'width')::NUMERIC,
                height = (v_position->>'height')::NUMERIC,
                updated_at = NOW()
            WHERE id = v_element.id;
        END IF;
    END LOOP;
    
    -- Set this layout as active
    UPDATE layouts
    SET is_active = TRUE
    WHERE id = p_layout_id;
END;
$$ LANGUAGE plpgsql;

-- Function to capture current layout from diagram
CREATE OR REPLACE FUNCTION capture_diagram_layout(
    p_diagram_id UUID,
    p_layout_name VARCHAR(255),
    p_layout_type layout_type,
    p_user_id UUID
)
RETURNS UUID AS $$
DECLARE
    v_layout_id UUID;
    v_layout_data JSONB;
BEGIN
    -- Build layout_data from current diagram element positions
    SELECT jsonb_object_agg(
        concept_id::TEXT,
        jsonb_build_object(
            'x', position_x,
            'y', position_y,
            'width', width,
            'height', height
        )
    ) INTO v_layout_data
    FROM diagram_elements
    WHERE diagram_id = p_diagram_id
    AND is_visible = TRUE;
    
    -- Create new layout
    INSERT INTO layouts (
        diagram_id,
        name,
        layout_type,
        layout_data,
        created_by
    ) VALUES (
        p_diagram_id,
        p_layout_name,
        p_layout_type,
        v_layout_data,
        p_user_id
    )
    RETURNING id INTO v_layout_id;
    
    RETURN v_layout_id;
END;
$$ LANGUAGE plpgsql;

-- Function to restore layout from snapshot
CREATE OR REPLACE FUNCTION restore_layout_from_snapshot(
    p_snapshot_id UUID,
    p_user_id UUID
)
RETURNS BOOLEAN AS $$
DECLARE
    v_snapshot RECORD;
BEGIN
    -- Get snapshot data
    SELECT * INTO v_snapshot
    FROM layout_snapshots
    WHERE id = p_snapshot_id;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Snapshot not found';
    END IF;
    
    -- Update layout with snapshot data
    UPDATE layouts
    SET 
        layout_data = v_snapshot.layout_data,
        updated_by = p_user_id,
        updated_at = NOW()
    WHERE id = v_snapshot.layout_id;
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- Function to get layout history
CREATE OR REPLACE FUNCTION get_layout_history(p_layout_id UUID)
RETURNS TABLE (
    snapshot_id UUID,
    snapshot_name VARCHAR(255),
    created_by_id UUID,
    created_by_name VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE,
    is_current BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ls.id,
        ls.snapshot_name,
        ls.created_by,
        u.full_name,
        ls.created_at,
        (ls.layout_data = l.layout_data) as is_current
    FROM layout_snapshots ls
    JOIN users u ON u.id = ls.created_by
    JOIN layouts l ON l.id = ls.layout_id
    WHERE ls.layout_id = p_layout_id
    ORDER BY ls.created_at DESC;
END;
$$ LANGUAGE plpgsql STABLE;

-- Function to clone layout
CREATE OR REPLACE FUNCTION clone_layout(
    p_source_layout_id UUID,
    p_new_name VARCHAR(255),
    p_user_id UUID
)
RETURNS UUID AS $$
DECLARE
    v_new_layout_id UUID;
    v_source_layout RECORD;
BEGIN
    -- Get source layout
    SELECT * INTO v_source_layout
    FROM layouts
    WHERE id = p_source_layout_id
    AND deleted_at IS NULL;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Source layout not found';
    END IF;
    
    -- Create new layout
    INSERT INTO layouts (
        diagram_id,
        name,
        description,
        layout_type,
        layout_data,
        constraints,
        settings,
        is_auto_apply,
        created_by
    ) VALUES (
        v_source_layout.diagram_id,
        p_new_name,
        v_source_layout.description,
        v_source_layout.layout_type,
        v_source_layout.layout_data,
        v_source_layout.constraints,
        v_source_layout.settings,
        FALSE,
        p_user_id
    )
    RETURNING id INTO v_new_layout_id;
    
    RETURN v_new_layout_id;
END;
$$ LANGUAGE plpgsql;

-- Function to clean old layout snapshots (keep last N per layout)
CREATE OR REPLACE FUNCTION cleanup_old_layout_snapshots(
    p_layout_id UUID,
    p_keep_count INTEGER DEFAULT 10
)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM layout_snapshots
    WHERE id IN (
        SELECT id
        FROM layout_snapshots
        WHERE layout_id = p_layout_id
        ORDER BY created_at DESC
        OFFSET p_keep_count
    );
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Logging
DO $$
BEGIN
    RAISE NOTICE 'Layouts schema created successfully';
END $$;