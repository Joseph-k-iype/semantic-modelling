-- database/postgres/schema/02-workspaces.sql
-- Workspaces table - Organizational containers for models
-- Path: database/postgres/schema/02-workspaces.sql

-- Workspace types enum (created in init script, but safe to check)
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'workspace_type') THEN
        CREATE TYPE workspace_type AS ENUM ('personal', 'team', 'common');
    END IF;
END $$;

-- ============================================================================
-- WORKSPACES TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS workspaces (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Workspace type
    type workspace_type NOT NULL DEFAULT 'personal',
    
    -- Ownership
    created_by UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    
    -- Settings
    settings JSONB DEFAULT '{}'::JSONB,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    -- Soft delete support
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    -- For personal workspaces, ensure one per user
    CONSTRAINT unique_personal_workspace UNIQUE NULLS NOT DISTINCT (created_by, type) 
        DEFERRABLE INITIALLY DEFERRED,
    CONSTRAINT workspace_name_length CHECK (char_length(name) >= 1 AND char_length(name) <= 255)
);

-- ============================================================================
-- WORKSPACE MEMBERS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS workspace_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Role in workspace
    role VARCHAR(50) NOT NULL DEFAULT 'viewer',
    
    -- Permissions
    can_view BOOLEAN DEFAULT TRUE NOT NULL,
    can_edit BOOLEAN DEFAULT FALSE NOT NULL,
    can_delete BOOLEAN DEFAULT FALSE NOT NULL,
    can_publish BOOLEAN DEFAULT FALSE NOT NULL,
    can_manage_members BOOLEAN DEFAULT FALSE NOT NULL,
    
    -- Timestamps
    added_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    added_by UUID REFERENCES users(id) ON DELETE SET NULL,
    
    -- Constraints
    CONSTRAINT unique_workspace_member UNIQUE (workspace_id, user_id),
    CONSTRAINT valid_role CHECK (role IN ('viewer', 'editor', 'publisher', 'admin'))
);

-- ============================================================================
-- WORKSPACE INVITATIONS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS workspace_invitations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'viewer',
    
    -- Invitation token
    token VARCHAR(255) UNIQUE NOT NULL,
    
    -- Status
    status VARCHAR(50) DEFAULT 'pending' NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    
    -- Audit
    invited_by UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    invited_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    accepted_at TIMESTAMP WITH TIME ZONE,
    accepted_by UUID REFERENCES users(id) ON DELETE SET NULL,
    
    -- Constraints
    CONSTRAINT valid_invitation_role CHECK (role IN ('viewer', 'editor', 'publisher', 'admin')),
    CONSTRAINT valid_invitation_status CHECK (status IN ('pending', 'accepted', 'declined', 'expired'))
);

-- ============================================================================
-- INDEXES
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_workspaces_created_by ON workspaces(created_by);
CREATE INDEX IF NOT EXISTS idx_workspaces_type ON workspaces(type);
CREATE INDEX IF NOT EXISTS idx_workspaces_is_active ON workspaces(is_active);
CREATE INDEX IF NOT EXISTS idx_workspaces_created_at ON workspaces(created_at);
CREATE INDEX IF NOT EXISTS idx_workspaces_deleted_at ON workspaces(deleted_at);

CREATE INDEX IF NOT EXISTS idx_workspace_members_workspace_id ON workspace_members(workspace_id);
CREATE INDEX IF NOT EXISTS idx_workspace_members_user_id ON workspace_members(user_id);
CREATE INDEX IF NOT EXISTS idx_workspace_members_role ON workspace_members(role);

CREATE INDEX IF NOT EXISTS idx_workspace_invitations_workspace_id ON workspace_invitations(workspace_id);
CREATE INDEX IF NOT EXISTS idx_workspace_invitations_email ON workspace_invitations(email);
CREATE INDEX IF NOT EXISTS idx_workspace_invitations_token ON workspace_invitations(token);
CREATE INDEX IF NOT EXISTS idx_workspace_invitations_status ON workspace_invitations(status);

-- ============================================================================
-- TRIGGERS
-- ============================================================================
CREATE TRIGGER update_workspaces_updated_at
    BEFORE UPDATE ON workspaces
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- COMMENTS
-- ============================================================================
COMMENT ON TABLE workspaces IS 'Organizational containers for models and diagrams';
COMMENT ON COLUMN workspaces.type IS 'Workspace type: personal, team, or common';
COMMENT ON COLUMN workspaces.deleted_at IS 'Soft delete timestamp - workspace is deleted if not null';
COMMENT ON TABLE workspace_members IS 'Users who have access to a workspace';
COMMENT ON TABLE workspace_invitations IS 'Pending workspace invitations';