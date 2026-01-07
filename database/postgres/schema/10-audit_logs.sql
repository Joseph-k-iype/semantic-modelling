-- =====================================================
-- Audit Logs System - Complete Implementation
-- =====================================================
-- Purpose: Track all changes to critical tables for compliance and debugging
-- Features: 
--   - Automatic audit logging via triggers
--   - Stores old/new values as JSONB for flexibility
--   - Tracks user, IP, and user agent
--   - Optimized indexes for common queries

-- =====================================================
-- STEP 1: Clean up existing objects (in correct order)
-- =====================================================

-- Drop triggers first (they depend on function)
DROP TRIGGER IF EXISTS audit_trigger_users ON users CASCADE;
DROP TRIGGER IF EXISTS audit_trigger_workspaces ON workspaces CASCADE;
DROP TRIGGER IF EXISTS audit_trigger_projects ON projects CASCADE;
DROP TRIGGER IF EXISTS audit_trigger_diagrams ON diagrams CASCADE;
DROP TRIGGER IF EXISTS audit_trigger_models ON models CASCADE;
DROP TRIGGER IF EXISTS audit_trigger_elements ON elements CASCADE;
DROP TRIGGER IF EXISTS audit_trigger_relationships ON relationships CASCADE;
DROP TRIGGER IF EXISTS audit_trigger_attributes ON attributes CASCADE;
DROP TRIGGER IF EXISTS audit_trigger_collaboration_sessions ON collaboration_sessions CASCADE;
DROP TRIGGER IF EXISTS audit_trigger_comments ON comments CASCADE;

-- Drop functions (they depend on types)
DROP FUNCTION IF EXISTS audit_trigger_function() CASCADE;
DROP FUNCTION IF EXISTS get_audit_action(text) CASCADE;
DROP FUNCTION IF EXISTS get_user_from_record(jsonb, text) CASCADE;

-- Drop table (it depends on type)
DROP TABLE IF EXISTS audit_logs CASCADE;

-- Drop type last
DROP TYPE IF EXISTS audit_action CASCADE;

-- =====================================================
-- STEP 2: Create the audit_action enum type
-- =====================================================

CREATE TYPE audit_action AS ENUM (
    'CREATE',      -- Insert operation
    'UPDATE',      -- Update operation
    'DELETE',      -- Delete operation
    'LOGIN',       -- User login event
    'LOGOUT',      -- User logout event
    'ACCESS',      -- Resource access event
    'EXPORT',      -- Data export event
    'IMPORT',      -- Data import event
    'SHARE',       -- Resource sharing event
    'PUBLISH',     -- Publishing event
    'ARCHIVE'      -- Archiving event
);

COMMENT ON TYPE audit_action IS 'Enumeration of possible audit actions';

-- =====================================================
-- STEP 3: Create audit_logs table
-- =====================================================

CREATE TABLE audit_logs (
    -- Primary identification
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- User who performed the action
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    
    -- Action type
    action audit_action NOT NULL,
    
    -- Affected resource
    table_name VARCHAR(100),
    record_id UUID,
    
    -- Change tracking
    old_values JSONB,
    new_values JSONB,
    
    -- Session information
    ip_address INET,
    user_agent TEXT,
    session_id VARCHAR(255),
    
    -- Additional context
    metadata JSONB DEFAULT '{}'::jsonb,
    
    -- Timestamp
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT check_values_present CHECK (
        (action = 'CREATE' AND new_values IS NOT NULL) OR
        (action = 'UPDATE' AND old_values IS NOT NULL AND new_values IS NOT NULL) OR
        (action = 'DELETE' AND old_values IS NOT NULL) OR
        (action NOT IN ('CREATE', 'UPDATE', 'DELETE'))
    )
);

-- Table comments
COMMENT ON TABLE audit_logs IS 'Comprehensive audit log for all database changes';
COMMENT ON COLUMN audit_logs.id IS 'Unique identifier for audit log entry';
COMMENT ON COLUMN audit_logs.user_id IS 'User who performed the action (NULL if system or deleted user)';
COMMENT ON COLUMN audit_logs.action IS 'Type of action performed';
COMMENT ON COLUMN audit_logs.table_name IS 'Name of the affected table';
COMMENT ON COLUMN audit_logs.record_id IS 'ID of the affected record';
COMMENT ON COLUMN audit_logs.old_values IS 'Complete record state before change (JSON)';
COMMENT ON COLUMN audit_logs.new_values IS 'Complete record state after change (JSON)';
COMMENT ON COLUMN audit_logs.ip_address IS 'IP address of the client';
COMMENT ON COLUMN audit_logs.user_agent IS 'User agent string from client';
COMMENT ON COLUMN audit_logs.session_id IS 'Session identifier';
COMMENT ON COLUMN audit_logs.metadata IS 'Additional context (request info, custom data, etc.)';
COMMENT ON COLUMN audit_logs.created_at IS 'Timestamp when audit log was created';

-- =====================================================
-- STEP 4: Create indexes for query optimization
-- =====================================================

-- Primary lookup indexes
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id) WHERE user_id IS NOT NULL;
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_table_name ON audit_logs(table_name) WHERE table_name IS NOT NULL;
CREATE INDEX idx_audit_logs_record_id ON audit_logs(record_id) WHERE record_id IS NOT NULL;

-- Time-based queries (most common)
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at DESC);

-- Composite indexes for common query patterns
CREATE INDEX idx_audit_logs_table_record ON audit_logs(table_name, record_id) 
    WHERE table_name IS NOT NULL AND record_id IS NOT NULL;
CREATE INDEX idx_audit_logs_user_action ON audit_logs(user_id, action) 
    WHERE user_id IS NOT NULL;
CREATE INDEX idx_audit_logs_user_created ON audit_logs(user_id, created_at DESC) 
    WHERE user_id IS NOT NULL;

-- JSONB indexes for metadata queries
CREATE INDEX idx_audit_logs_metadata_gin ON audit_logs USING GIN (metadata);

-- Session tracking
CREATE INDEX idx_audit_logs_session ON audit_logs(session_id) 
    WHERE session_id IS NOT NULL;

-- =====================================================
-- STEP 5: Helper functions
-- =====================================================

-- Function to safely convert text to audit_action enum
CREATE OR REPLACE FUNCTION get_audit_action(action_text text)
RETURNS audit_action AS $$
BEGIN
    RETURN action_text::audit_action;
EXCEPTION 
    WHEN invalid_text_representation THEN
        RETURN 'UPDATE'::audit_action;  -- Default fallback
    WHEN OTHERS THEN
        RETURN 'UPDATE'::audit_action;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION get_audit_action(text) IS 'Safely convert text to audit_action enum with fallback';

-- Function to extract user_id from record
CREATE OR REPLACE FUNCTION get_user_from_record(record_data jsonb, operation text)
RETURNS UUID AS $$
DECLARE
    user_uuid UUID;
BEGIN
    -- Try to get user_id from various possible fields
    IF record_data ? 'owner_id' THEN
        user_uuid := (record_data->>'owner_id')::UUID;
    ELSIF record_data ? 'created_by' THEN
        user_uuid := (record_data->>'created_by')::UUID;
    ELSIF record_data ? 'user_id' THEN
        user_uuid := (record_data->>'user_id')::UUID;
    ELSIF record_data ? 'modified_by' THEN
        user_uuid := (record_data->>'modified_by')::UUID;
    ELSE
        user_uuid := NULL;
    END IF;
    
    RETURN user_uuid;
EXCEPTION
    WHEN OTHERS THEN
        RETURN NULL;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION get_user_from_record(jsonb, text) IS 'Extract user UUID from record data';

-- =====================================================
-- STEP 6: Main audit trigger function
-- =====================================================

CREATE OR REPLACE FUNCTION audit_trigger_function()
RETURNS TRIGGER AS $$
DECLARE
    v_action audit_action;
    v_old_values JSONB;
    v_new_values JSONB;
    v_user_id UUID;
    v_record_id UUID;
BEGIN
    -- Determine action type
    IF TG_OP = 'INSERT' THEN
        v_action := 'CREATE'::audit_action;
        v_old_values := NULL;
        v_new_values := to_jsonb(NEW);
        v_record_id := NEW.id;
        v_user_id := get_user_from_record(v_new_values, TG_OP);
        
    ELSIF TG_OP = 'UPDATE' THEN
        v_action := 'UPDATE'::audit_action;
        v_old_values := to_jsonb(OLD);
        v_new_values := to_jsonb(NEW);
        v_record_id := NEW.id;
        v_user_id := get_user_from_record(v_new_values, TG_OP);
        
    ELSIF TG_OP = 'DELETE' THEN
        v_action := 'DELETE'::audit_action;
        v_old_values := to_jsonb(OLD);
        v_new_values := NULL;
        v_record_id := OLD.id;
        v_user_id := get_user_from_record(v_old_values, TG_OP);
        
    ELSE
        -- Unknown operation, skip audit
        IF TG_OP = 'DELETE' THEN
            RETURN OLD;
        ELSE
            RETURN NEW;
        END IF;
    END IF;

    -- Insert audit log entry
    BEGIN
        INSERT INTO audit_logs (
            user_id,
            action,
            table_name,
            record_id,
            old_values,
            new_values,
            metadata
        ) VALUES (
            v_user_id,
            v_action,
            TG_TABLE_NAME,
            v_record_id,
            v_old_values,
            v_new_values,
            jsonb_build_object(
                'schema', TG_TABLE_SCHEMA,
                'operation', TG_OP,
                'level', TG_LEVEL,
                'when', TG_WHEN
            )
        );
    EXCEPTION
        WHEN OTHERS THEN
            -- Log error but don't fail the original operation
            RAISE WARNING 'Failed to create audit log for %.%: %', TG_TABLE_SCHEMA, TG_TABLE_NAME, SQLERRM;
    END;

    -- Return appropriate value
    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    ELSE
        RETURN NEW;
    END IF;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION audit_trigger_function() IS 'Generic trigger function for audit logging';

-- =====================================================
-- STEP 7: Apply triggers to tables
-- =====================================================

-- Helper function to create audit trigger
CREATE OR REPLACE FUNCTION create_audit_trigger(table_name text)
RETURNS void AS $$
DECLARE
    trigger_name text;
BEGIN
    trigger_name := 'audit_trigger_' || table_name;
    
    EXECUTE format('
        CREATE TRIGGER %I
        AFTER INSERT OR UPDATE OR DELETE ON %I
        FOR EACH ROW EXECUTE FUNCTION audit_trigger_function()',
        trigger_name, table_name
    );
    
    RAISE NOTICE 'Created audit trigger for table: %', table_name;
EXCEPTION
    WHEN undefined_table THEN
        RAISE NOTICE 'Table % does not exist, skipping audit trigger', table_name;
    WHEN duplicate_object THEN
        RAISE NOTICE 'Audit trigger already exists for table: %', table_name;
END;
$$ LANGUAGE plpgsql;

-- Apply triggers to all relevant tables
DO $$
DECLARE
    tables_to_audit text[] := ARRAY[
        'users',
        'workspaces',
        'projects',
        'diagrams',
        'models',
        'elements',
        'relationships',
        'attributes',
        'collaboration_sessions',
        'collaboration_participants',
        'comments',
        'shares',
        'notifications',
        'api_keys',
        'webhooks'
    ];
    table_name text;
BEGIN
    FOREACH table_name IN ARRAY tables_to_audit
    LOOP
        PERFORM create_audit_trigger(table_name);
    END LOOP;
END $$;

-- Drop the helper function (no longer needed)
DROP FUNCTION IF EXISTS create_audit_trigger(text);

-- =====================================================
-- STEP 8: Utility views for common queries
-- =====================================================

-- View for recent activity
CREATE OR REPLACE VIEW v_recent_audit_activity AS
SELECT 
    al.id,
    al.created_at,
    al.action,
    al.table_name,
    al.record_id,
    u.username,
    u.email,
    al.ip_address
FROM audit_logs al
LEFT JOIN users u ON al.user_id = u.id
ORDER BY al.created_at DESC
LIMIT 1000;

COMMENT ON VIEW v_recent_audit_activity IS 'Recent 1000 audit log entries with user information';

-- View for user activity summary
CREATE OR REPLACE VIEW v_user_audit_summary AS
SELECT 
    u.id as user_id,
    u.username,
    u.email,
    COUNT(*) as total_actions,
    COUNT(*) FILTER (WHERE al.action = 'CREATE') as creates,
    COUNT(*) FILTER (WHERE al.action = 'UPDATE') as updates,
    COUNT(*) FILTER (WHERE al.action = 'DELETE') as deletes,
    MAX(al.created_at) as last_activity
FROM users u
LEFT JOIN audit_logs al ON u.id = al.user_id
GROUP BY u.id, u.username, u.email;

COMMENT ON VIEW v_user_audit_summary IS 'Summary of audit activity by user';

-- =====================================================
-- STEP 9: Maintenance functions
-- =====================================================

-- Function to clean up old audit logs
CREATE OR REPLACE FUNCTION cleanup_old_audit_logs(days_to_keep integer DEFAULT 90)
RETURNS integer AS $$
DECLARE
    deleted_count integer;
BEGIN
    DELETE FROM audit_logs
    WHERE created_at < CURRENT_TIMESTAMP - (days_to_keep || ' days')::interval;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    RAISE NOTICE 'Deleted % audit log entries older than % days', deleted_count, days_to_keep;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION cleanup_old_audit_logs(integer) IS 'Delete audit logs older than specified days (default: 90)';

-- Function to get audit trail for a specific record
CREATE OR REPLACE FUNCTION get_audit_trail(
    p_table_name text,
    p_record_id uuid
)
RETURNS TABLE (
    log_id uuid,
    action audit_action,
    changed_at timestamp with time zone,
    changed_by_username text,
    changed_by_email text,
    old_values jsonb,
    new_values jsonb
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        al.id as log_id,
        al.action,
        al.created_at as changed_at,
        u.username as changed_by_username,
        u.email as changed_by_email,
        al.old_values,
        al.new_values
    FROM audit_logs al
    LEFT JOIN users u ON al.user_id = u.id
    WHERE al.table_name = p_table_name
      AND al.record_id = p_record_id
    ORDER BY al.created_at DESC;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_audit_trail(text, uuid) IS 'Get complete audit trail for a specific record';

-- =====================================================
-- STEP 10: Grant permissions
-- =====================================================

-- Grant read access to audit logs (adjust role name as needed)
-- GRANT SELECT ON audit_logs TO read_only_role;
-- GRANT SELECT ON v_recent_audit_activity TO read_only_role;
-- GRANT SELECT ON v_user_audit_summary TO read_only_role;

-- =====================================================
-- STEP 11: Verification
-- =====================================================

-- Verify enum type was created
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'audit_action') THEN
        RAISE NOTICE '✓ audit_action enum type created successfully';
    ELSE
        RAISE EXCEPTION '✗ audit_action enum type was not created';
    END IF;
END $$;

-- Verify table was created
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'audit_logs') THEN
        RAISE NOTICE '✓ audit_logs table created successfully';
    ELSE
        RAISE EXCEPTION '✗ audit_logs table was not created';
    END IF;
END $$;

-- Verify triggers were created
DO $$
DECLARE
    trigger_count integer;
BEGIN
    SELECT COUNT(*) INTO trigger_count
    FROM information_schema.triggers
    WHERE trigger_name LIKE 'audit_trigger_%';
    
    RAISE NOTICE '✓ Created % audit triggers', trigger_count;
END $$;

-- Display summary
DO $$
DECLARE
    enum_count integer;
    table_count integer;
    index_count integer;
    trigger_count integer;
    function_count integer;
    view_count integer;
BEGIN
    -- Count objects
    SELECT COUNT(*) INTO enum_count FROM pg_type WHERE typname = 'audit_action';
    SELECT COUNT(*) INTO table_count FROM information_schema.tables WHERE table_name = 'audit_logs';
    SELECT COUNT(*) INTO index_count FROM pg_indexes WHERE tablename = 'audit_logs';
    SELECT COUNT(*) INTO trigger_count FROM information_schema.triggers WHERE trigger_name LIKE 'audit_trigger_%';
    SELECT COUNT(*) INTO function_count FROM pg_proc WHERE proname IN ('audit_trigger_function', 'get_audit_action', 'get_user_from_record', 'cleanup_old_audit_logs', 'get_audit_trail');
    SELECT COUNT(*) INTO view_count FROM information_schema.views WHERE table_name LIKE 'v_%audit%';
    
    RAISE NOTICE '================================================';
    RAISE NOTICE 'Audit System Installation Summary';
    RAISE NOTICE '================================================';
    RAISE NOTICE 'Enum Types: %', enum_count;
    RAISE NOTICE 'Tables: %', table_count;
    RAISE NOTICE 'Indexes: %', index_count;
    RAISE NOTICE 'Triggers: %', trigger_count;
    RAISE NOTICE 'Functions: %', function_count;
    RAISE NOTICE 'Views: %', view_count;
    RAISE NOTICE '================================================';
    RAISE NOTICE 'Audit logging system is now active!';
    RAISE NOTICE '================================================';
END $$;