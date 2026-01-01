-- database/postgres/schema/10-audit_logs.sql
-- Audit logs for comprehensive tracking of all system changes

-- Drop existing tables if exist (for clean reinstall)
DROP TABLE IF EXISTS audit_logs CASCADE;

-- Audit logs table
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_type entity_type NOT NULL,
    entity_id UUID NOT NULL,
    action audit_action NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    workspace_id UUID REFERENCES workspaces(id) ON DELETE SET NULL,
    old_values JSONB,
    new_values JSONB,
    changes JSONB,
    metadata JSONB DEFAULT '{}'::JSONB,
    ip_address INET,
    user_agent TEXT,
    request_id VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Partition audit_logs by month for better performance
-- Note: In production, you would create partitions programmatically
-- This is a base table that can be partitioned

-- Indexes for audit_logs table
CREATE INDEX idx_audit_logs_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_workspace_id ON audit_logs(workspace_id);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at DESC);
CREATE INDEX idx_audit_logs_request_id ON audit_logs(request_id) WHERE request_id IS NOT NULL;

-- GIN index for changes JSONB
CREATE INDEX idx_audit_logs_changes ON audit_logs USING gin(changes);

-- Composite index for common queries
CREATE INDEX idx_audit_logs_entity_time ON audit_logs(entity_type, entity_id, created_at DESC);
CREATE INDEX idx_audit_logs_user_time ON audit_logs(user_id, created_at DESC);

-- Function to create audit log
CREATE OR REPLACE FUNCTION create_audit_log(
    p_entity_type entity_type,
    p_entity_id UUID,
    p_action audit_action,
    p_user_id UUID,
    p_workspace_id UUID DEFAULT NULL,
    p_old_values JSONB DEFAULT NULL,
    p_new_values JSONB DEFAULT NULL,
    p_metadata JSONB DEFAULT '{}'::JSONB
)
RETURNS UUID AS $$
DECLARE
    v_audit_id UUID;
    v_changes JSONB;
BEGIN
    -- Calculate changes if both old and new values provided
    IF p_old_values IS NOT NULL AND p_new_values IS NOT NULL THEN
        v_changes := jsonb_object_agg(
            key,
            jsonb_build_object(
                'old', p_old_values->key,
                'new', p_new_values->key
            )
        )
        FROM jsonb_each(p_new_values)
        WHERE p_old_values->key IS DISTINCT FROM p_new_values->key;
    END IF;
    
    -- Insert audit log
    INSERT INTO audit_logs (
        entity_type,
        entity_id,
        action,
        user_id,
        workspace_id,
        old_values,
        new_values,
        changes,
        metadata
    ) VALUES (
        p_entity_type,
        p_entity_id,
        p_action,
        p_user_id,
        p_workspace_id,
        p_old_values,
        p_new_values,
        v_changes,
        p_metadata
    )
    RETURNING id INTO v_audit_id;
    
    RETURN v_audit_id;
END;
$$ LANGUAGE plpgsql;

-- Generic trigger function to log all changes
CREATE OR REPLACE FUNCTION audit_trigger_function()
RETURNS TRIGGER AS $$
DECLARE
    v_entity_type entity_type;
    v_action audit_action;
    v_old_values JSONB;
    v_new_values JSONB;
    v_user_id UUID;
    v_workspace_id UUID;
BEGIN
    -- Determine entity type from table name
    v_entity_type := CASE TG_TABLE_NAME
        WHEN 'users' THEN 'USER'
        WHEN 'workspaces' THEN 'WORKSPACE'
        WHEN 'folders' THEN 'FOLDER'
        WHEN 'models' THEN 'MODEL'
        WHEN 'diagrams' THEN 'DIAGRAM'
        WHEN 'layouts' THEN 'LAYOUT'
        WHEN 'versions' THEN 'VERSION'
        WHEN 'publish_requests' THEN 'PUBLISH_WORKFLOW'
        WHEN 'comments' THEN 'COMMENT'
        ELSE NULL
    END;
    
    -- Skip if entity type not recognized
    IF v_entity_type IS NULL THEN
        RETURN COALESCE(NEW, OLD);
    END IF;
    
    -- Determine action
    v_action := CASE TG_OP
        WHEN 'INSERT' THEN 'CREATE'
        WHEN 'UPDATE' THEN 'UPDATE'
        WHEN 'DELETE' THEN 'DELETE'
    END;
    
    -- Extract user_id and workspace_id if available
    IF TG_OP = 'DELETE' THEN
        v_user_id := OLD.updated_by;
        v_workspace_id := CASE WHEN TG_TABLE_NAME IN ('models', 'folders') 
                          THEN OLD.workspace_id ELSE NULL END;
        v_old_values := row_to_json(OLD)::JSONB;
    ELSE
        v_user_id := NEW.updated_by;
        v_workspace_id := CASE WHEN TG_TABLE_NAME IN ('models', 'folders') 
                          THEN NEW.workspace_id ELSE NULL END;
        v_new_values := row_to_json(NEW)::JSONB;
        
        IF TG_OP = 'UPDATE' THEN
            v_old_values := row_to_json(OLD)::JSONB;
        END IF;
    END IF;
    
    -- Create audit log
    PERFORM create_audit_log(
        v_entity_type,
        COALESCE(NEW.id, OLD.id),
        v_action,
        v_user_id,
        v_workspace_id,
        v_old_values,
        v_new_values
    );
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Apply audit trigger to key tables
CREATE TRIGGER audit_models
    AFTER INSERT OR UPDATE OR DELETE ON models
    FOR EACH ROW
    EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_diagrams
    AFTER INSERT OR UPDATE OR DELETE ON diagrams
    FOR EACH ROW
    EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_layouts
    AFTER INSERT OR UPDATE OR DELETE ON layouts
    FOR EACH ROW
    EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_versions
    AFTER INSERT OR UPDATE OR DELETE ON versions
    FOR EACH ROW
    EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_publish_requests
    AFTER INSERT OR UPDATE OR DELETE ON publish_requests
    FOR EACH ROW
    EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_workspaces
    AFTER INSERT OR UPDATE OR DELETE ON workspaces
    FOR EACH ROW
    EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_folders
    AFTER INSERT OR UPDATE OR DELETE ON folders
    FOR EACH ROW
    EXECUTE FUNCTION audit_trigger_function();

-- Function to get audit trail for entity
CREATE OR REPLACE FUNCTION get_audit_trail(
    p_entity_type entity_type,
    p_entity_id UUID,
    p_limit INTEGER DEFAULT 100
)
RETURNS TABLE (
    audit_id UUID,
    action audit_action,
    user_name VARCHAR(255),
    changes JSONB,
    created_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        al.id,
        al.action,
        u.full_name,
        al.changes,
        al.created_at
    FROM audit_logs al
    LEFT JOIN users u ON u.id = al.user_id
    WHERE al.entity_type = p_entity_type
    AND al.entity_id = p_entity_id
    ORDER BY al.created_at DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql STABLE;

-- Function to get user activity
CREATE OR REPLACE FUNCTION get_user_activity(
    p_user_id UUID,
    p_limit INTEGER DEFAULT 100
)
RETURNS TABLE (
    audit_id UUID,
    entity_type entity_type,
    entity_id UUID,
    action audit_action,
    workspace_name VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        al.id,
        al.entity_type,
        al.entity_id,
        al.action,
        w.name,
        al.created_at
    FROM audit_logs al
    LEFT JOIN workspaces w ON w.id = al.workspace_id
    WHERE al.user_id = p_user_id
    ORDER BY al.created_at DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql STABLE;

-- Function to get workspace activity
CREATE OR REPLACE FUNCTION get_workspace_activity(
    p_workspace_id UUID,
    p_limit INTEGER DEFAULT 100
)
RETURNS TABLE (
    audit_id UUID,
    entity_type entity_type,
    entity_id UUID,
    action audit_action,
    user_name VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        al.id,
        al.entity_type,
        al.entity_id,
        al.action,
        u.full_name,
        al.created_at
    FROM audit_logs al
    LEFT JOIN users u ON u.id = al.user_id
    WHERE al.workspace_id = p_workspace_id
    ORDER BY al.created_at DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql STABLE;

-- Function to get recent activity across system
CREATE OR REPLACE FUNCTION get_recent_activity(
    p_limit INTEGER DEFAULT 100
)
RETURNS TABLE (
    audit_id UUID,
    entity_type entity_type,
    entity_id UUID,
    action audit_action,
    user_name VARCHAR(255),
    workspace_name VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        al.id,
        al.entity_type,
        al.entity_id,
        al.action,
        u.full_name,
        w.name,
        al.created_at
    FROM audit_logs al
    LEFT JOIN users u ON u.id = al.user_id
    LEFT JOIN workspaces w ON w.id = al.workspace_id
    ORDER BY al.created_at DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql STABLE;

-- Function to search audit logs
CREATE OR REPLACE FUNCTION search_audit_logs(
    p_search_term TEXT,
    p_entity_type entity_type DEFAULT NULL,
    p_action audit_action DEFAULT NULL,
    p_user_id UUID DEFAULT NULL,
    p_workspace_id UUID DEFAULT NULL,
    p_from_date TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    p_to_date TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    p_limit INTEGER DEFAULT 100
)
RETURNS TABLE (
    audit_id UUID,
    entity_type entity_type,
    entity_id UUID,
    action audit_action,
    user_name VARCHAR(255),
    workspace_name VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        al.id,
        al.entity_type,
        al.entity_id,
        al.action,
        u.full_name,
        w.name,
        al.created_at
    FROM audit_logs al
    LEFT JOIN users u ON u.id = al.user_id
    LEFT JOIN workspaces w ON w.id = al.workspace_id
    WHERE (p_entity_type IS NULL OR al.entity_type = p_entity_type)
    AND (p_action IS NULL OR al.action = p_action)
    AND (p_user_id IS NULL OR al.user_id = p_user_id)
    AND (p_workspace_id IS NULL OR al.workspace_id = p_workspace_id)
    AND (p_from_date IS NULL OR al.created_at >= p_from_date)
    AND (p_to_date IS NULL OR al.created_at <= p_to_date)
    AND (p_search_term IS NULL OR al.changes::TEXT ILIKE '%' || p_search_term || '%')
    ORDER BY al.created_at DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql STABLE;

-- Function to cleanup old audit logs (for data retention)
CREATE OR REPLACE FUNCTION cleanup_old_audit_logs(
    p_retention_days INTEGER DEFAULT 365
)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM audit_logs
    WHERE created_at < NOW() - (p_retention_days || ' days')::INTERVAL;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Create a scheduled job function (requires pg_cron extension)
-- This is commented out by default, uncomment if pg_cron is available
/*
CREATE EXTENSION IF NOT EXISTS pg_cron;

-- Schedule cleanup to run monthly
SELECT cron.schedule(
    'cleanup-old-audit-logs',
    '0 0 1 * *',  -- First day of every month at midnight
    'SELECT cleanup_old_audit_logs(365);'
);
*/

-- Logging
DO $$
BEGIN
    RAISE NOTICE 'Audit logs schema created successfully';
    RAISE NOTICE 'All database schema files created successfully!';
    RAISE NOTICE 'Execute these files in order: 01-init-db.sql, then 01-users.sql through 10-audit_logs.sql';
END $$;