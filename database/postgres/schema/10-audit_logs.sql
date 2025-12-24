-- Audit action enum
CREATE TYPE audit_action AS ENUM (
    'create', 'update', 'delete', 'read',
    'login', 'logout', 'login_failed',
    'publish_request', 'publish_approve', 'publish_reject',
    'share_create', 'share_access',
    'export', 'import'
);

-- Audit logs table
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Who performed the action
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    user_email VARCHAR(255), -- Denormalized for deleted users
    
    -- What was done
    action audit_action NOT NULL,
    entity_type VARCHAR(100), -- model, diagram, workspace, user, etc.
    entity_id UUID,
    
    -- Detailed changes
    old_values JSONB,
    new_values JSONB,
    
    -- Context
    workspace_id UUID REFERENCES workspaces(id) ON DELETE SET NULL,
    
    -- Request details
    ip_address INET,
    user_agent TEXT,
    request_id VARCHAR(100),
    
    -- Timestamp
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    -- Additional metadata
    metadata JSONB DEFAULT '{}'::JSONB,
    
    -- Success or failure
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT
);

-- Security events (login attempts, permission denials, etc.)
CREATE TABLE IF NOT EXISTS security_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Event type
    event_type VARCHAR(50) NOT NULL, -- login_success, login_failed, permission_denied, etc.
    
    -- User (may be null for failed login attempts)
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    email VARCHAR(255),
    
    -- Request details
    ip_address INET NOT NULL,
    user_agent TEXT,
    
    -- Event details
    details JSONB DEFAULT '{}'::JSONB,
    severity VARCHAR(20) DEFAULT 'info', -- info, warning, critical
    
    -- Timestamp
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    CONSTRAINT valid_severity CHECK (severity IN ('info', 'warning', 'critical'))
);

-- Data access logs (for compliance)
CREATE TABLE IF NOT EXISTS data_access_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Who accessed
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    
    -- What was accessed
    entity_type VARCHAR(100) NOT NULL,
    entity_id UUID NOT NULL,
    access_type VARCHAR(20) NOT NULL, -- read, export, share
    
    -- When and where
    accessed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    ip_address INET,
    
    -- Purpose (optional)
    purpose TEXT,
    
    CONSTRAINT valid_access_type CHECK (access_type IN ('read', 'export', 'share', 'print'))
);

-- Indexes for audit_logs
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX idx_audit_logs_workspace_id ON audit_logs(workspace_id);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);
CREATE INDEX idx_audit_logs_ip_address ON audit_logs(ip_address);
CREATE INDEX idx_audit_logs_request_id ON audit_logs(request_id);

-- Indexes for security_events
CREATE INDEX idx_security_events_user_id ON security_events(user_id);
CREATE INDEX idx_security_events_email ON security_events(email);
CREATE INDEX idx_security_events_event_type ON security_events(event_type);
CREATE INDEX idx_security_events_ip_address ON security_events(ip_address);
CREATE INDEX idx_security_events_severity ON security_events(severity);
CREATE INDEX idx_security_events_created_at ON security_events(created_at);

-- Indexes for data_access_logs
CREATE INDEX idx_data_access_logs_user_id ON data_access_logs(user_id);
CREATE INDEX idx_data_access_logs_entity ON data_access_logs(entity_type, entity_id);
CREATE INDEX idx_data_access_logs_access_type ON data_access_logs(access_type);
CREATE INDEX idx_data_access_logs_accessed_at ON data_access_logs(accessed_at);

-- Partitioning setup for audit_logs (by month)
-- This can be enabled for high-volume installations
-- CREATE TABLE audit_logs_y2024m01 PARTITION OF audit_logs
--     FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

-- Function to cleanup old audit logs
CREATE OR REPLACE FUNCTION cleanup_old_audit_logs()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
    retention_days INTEGER := 365; -- Get from settings
BEGIN
    DELETE FROM audit_logs
    WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '1 day' * retention_days;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Function to log model changes
CREATE OR REPLACE FUNCTION audit_model_changes()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO audit_logs (
            user_id, action, entity_type, entity_id,
            new_values, workspace_id
        ) VALUES (
            NEW.created_by, 'create', 'model', NEW.id,
            to_jsonb(NEW), NEW.workspace_id
        );
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO audit_logs (
            user_id, action, entity_type, entity_id,
            old_values, new_values, workspace_id
        ) VALUES (
            NEW.updated_by, 'update', 'model', NEW.id,
            to_jsonb(OLD), to_jsonb(NEW), NEW.workspace_id
        );
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO audit_logs (
            user_id, action, entity_type, entity_id,
            old_values, workspace_id
        ) VALUES (
            OLD.updated_by, 'delete', 'model', OLD.id,
            to_jsonb(OLD), OLD.workspace_id
        );
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER audit_model_changes_trigger
    AFTER INSERT OR UPDATE OR DELETE ON models
    FOR EACH ROW
    EXECUTE FUNCTION audit_model_changes();

-- View for recent activity
CREATE OR REPLACE VIEW recent_activity AS
SELECT 
    al.id,
    al.action,
    al.entity_type,
    al.entity_id,
    al.created_at,
    u.full_name as user_name,
    u.email as user_email,
    w.name as workspace_name,
    al.success
FROM audit_logs al
LEFT JOIN users u ON al.user_id = u.id
LEFT JOIN workspaces w ON al.workspace_id = w.id
ORDER BY al.created_at DESC
LIMIT 100;

-- View for security dashboard
CREATE OR REPLACE VIEW security_dashboard AS
SELECT 
    event_type,
    severity,
    COUNT(*) as event_count,
    COUNT(DISTINCT ip_address) as unique_ips,
    MAX(created_at) as last_occurrence
FROM security_events
WHERE created_at > CURRENT_TIMESTAMP - INTERVAL '24 hours'
GROUP BY event_type, severity
ORDER BY event_count DESC;

COMMENT ON TABLE audit_logs IS 'Complete audit trail of all system actions';
COMMENT ON TABLE security_events IS 'Security-related events for monitoring and compliance';
COMMENT ON TABLE data_access_logs IS 'Log of data access for compliance requirements';
COMMENT ON COLUMN audit_logs.request_id IS 'Trace ID for correlating related operations';