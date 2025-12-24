-- Workspace types enum
CREATE TYPE workspace_type AS ENUM ('personal', 'team', 'common');

-- Workspace roles enum
CREATE TYPE workspace_role AS ENUM ('viewer', 'editor', 'publisher', 'admin');

-- Workspaces table
CREATE TABLE IF NOT EXISTS workspaces (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    type workspace_type NOT NULL DEFAULT 'personal',
    owner_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    settings JSONB DEFAULT '{}'::JSONB,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    CONSTRAINT unique_personal_workspace UNIQUE (owner_id, type) 
        WHERE type = 'personal',
    CONSTRAINT unique_workspace_name_per_owner UNIQUE (owner_id, name)
);

-- Workspace members (users who have access to a workspace)
CREATE TABLE IF NOT EXISTS workspace_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role workspace_role NOT NULL DEFAULT 'viewer',
    invited_by UUID REFERENCES users(id) ON DELETE SET NULL,
    invited_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    joined_at TIMESTAMP WITH TIME ZONE,
    last_accessed_at TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT unique_workspace_member UNIQUE (workspace_id, user_id)
);

-- Workspace invitations
CREATE TABLE IF NOT EXISTS workspace_invitations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    role workspace_role NOT NULL DEFAULT 'viewer',
    invited_by UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    accepted_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    CONSTRAINT valid_invitation_expiry CHECK (expires_at > created_at),
    CONSTRAINT unique_pending_invitation UNIQUE (workspace_id, email) 
        WHERE accepted_at IS NULL
);

-- Workspace activity log
CREATE TABLE IF NOT EXISTS workspace_activity (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(100),
    entity_id UUID,
    metadata JSONB DEFAULT '{}'::JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Indexes for performance
CREATE INDEX idx_workspaces_owner_id ON workspaces(owner_id);
CREATE INDEX idx_workspaces_type ON workspaces(type);
CREATE INDEX idx_workspaces_is_active ON workspaces(is_active);
CREATE INDEX idx_workspaces_created_at ON workspaces(created_at);

CREATE INDEX idx_workspace_members_workspace_id ON workspace_members(workspace_id);
CREATE INDEX idx_workspace_members_user_id ON workspace_members(user_id);
CREATE INDEX idx_workspace_members_role ON workspace_members(role);
CREATE INDEX idx_workspace_members_composite ON workspace_members(workspace_id, user_id, role);

CREATE INDEX idx_workspace_invitations_workspace_id ON workspace_invitations(workspace_id);
CREATE INDEX idx_workspace_invitations_email ON workspace_invitations(email);
CREATE INDEX idx_workspace_invitations_token ON workspace_invitations(token);
CREATE INDEX idx_workspace_invitations_expires_at ON workspace_invitations(expires_at);

CREATE INDEX idx_workspace_activity_workspace_id ON workspace_activity(workspace_id);
CREATE INDEX idx_workspace_activity_user_id ON workspace_activity(user_id);
CREATE INDEX idx_workspace_activity_action ON workspace_activity(action);
CREATE INDEX idx_workspace_activity_created_at ON workspace_activity(created_at);
CREATE INDEX idx_workspace_activity_entity ON workspace_activity(entity_type, entity_id);

-- Triggers
CREATE TRIGGER update_workspaces_updated_at
    BEFORE UPDATE ON workspaces
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Function to automatically add owner as admin member
CREATE OR REPLACE FUNCTION add_owner_as_admin()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO workspace_members (workspace_id, user_id, role, joined_at)
    VALUES (NEW.id, NEW.owner_id, 'admin', CURRENT_TIMESTAMP);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER add_owner_as_workspace_admin
    AFTER INSERT ON workspaces
    FOR EACH ROW
    EXECUTE FUNCTION add_owner_as_admin();

-- Function to log workspace activity
CREATE OR REPLACE FUNCTION log_workspace_activity()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO workspace_activity (workspace_id, action, entity_type, entity_id)
        VALUES (NEW.workspace_id, 'member_joined', 'workspace_member', NEW.id);
    ELSIF TG_OP = 'UPDATE' AND OLD.role != NEW.role THEN
        INSERT INTO workspace_activity (workspace_id, action, entity_type, entity_id, metadata)
        VALUES (NEW.workspace_id, 'member_role_changed', 'workspace_member', NEW.id,
                jsonb_build_object('old_role', OLD.role, 'new_role', NEW.role));
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO workspace_activity (workspace_id, action, entity_type, entity_id)
        VALUES (OLD.workspace_id, 'member_removed', 'workspace_member', OLD.id);
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER log_workspace_member_activity
    AFTER INSERT OR UPDATE OR DELETE ON workspace_members
    FOR EACH ROW
    EXECUTE FUNCTION log_workspace_activity();

-- Function to delete expired invitations
CREATE OR REPLACE FUNCTION delete_expired_invitations()
RETURNS TRIGGER AS $$
BEGIN
    DELETE FROM workspace_invitations 
    WHERE expires_at < CURRENT_TIMESTAMP 
    AND accepted_at IS NULL;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- View for active workspace members with user details
CREATE OR REPLACE VIEW workspace_members_detailed AS
SELECT 
    wm.id,
    wm.workspace_id,
    wm.user_id,
    wm.role,
    wm.invited_at,
    wm.joined_at,
    wm.last_accessed_at,
    u.email,
    u.full_name,
    u.avatar_url,
    u.is_active as user_is_active
FROM workspace_members wm
JOIN users u ON wm.user_id = u.id;

-- Comments
COMMENT ON TABLE workspaces IS 'Workspaces for organizing models and collaboration';
COMMENT ON TABLE workspace_members IS 'Users who are members of workspaces';
COMMENT ON TABLE workspace_invitations IS 'Pending invitations to join workspaces';
COMMENT ON TABLE workspace_activity IS 'Activity log for workspace actions';

COMMENT ON COLUMN workspaces.type IS 'Type of workspace: personal (private), team (collaborative), or common (organization-wide)';
COMMENT ON COLUMN workspaces.settings IS 'Workspace-specific settings as JSON';
COMMENT ON COLUMN workspace_members.role IS 'User role in workspace: viewer, editor, publisher, or admin';