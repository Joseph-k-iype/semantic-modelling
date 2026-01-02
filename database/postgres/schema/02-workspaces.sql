-- database/postgres/schema/02-workspaces.sql
-- Workspaces and workspace membership tables
-- STRATEGIC FIX: Aligned with SQLAlchemy model exactly

-- Drop existing tables if exist (for clean reinstall)
DROP TABLE IF EXISTS workspace_invitations CASCADE;
DROP TABLE IF EXISTS workspace_members CASCADE;
DROP TABLE IF EXISTS workspaces CASCADE;

-- Workspaces table - MATCHES app/models/workspace.py EXACTLY
CREATE TABLE workspaces (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Basic information
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    
    -- Type (uses workspace_type enum)
    type workspace_type DEFAULT 'personal' NOT NULL,
    
    -- Ownership and tracking - STRATEGIC FIX: Uses created_by pattern (not owner_id)
    created_by UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    updated_by UUID REFERENCES users(id) ON DELETE SET NULL,
    deleted_by UUID REFERENCES users(id) ON DELETE SET NULL,
    
    -- Customization
    icon VARCHAR(50),
    color VARCHAR(7),  -- Hex color code
    
    -- Status flags
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    is_archived BOOLEAN DEFAULT FALSE NOT NULL,
    
    -- Settings and metadata - STRATEGIC FIX: meta_data not metadata
    settings JSONB DEFAULT '{}'::JSONB NOT NULL,
    meta_data JSONB DEFAULT '{}'::JSONB NOT NULL,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    CONSTRAINT workspaces_name_check CHECK (LENGTH(TRIM(name)) >= 1),
    CONSTRAINT workspaces_slug_check CHECK (slug ~* '^[a-z0-9-]{3,100}$'),
    CONSTRAINT workspaces_color_check CHECK (color IS NULL OR color ~* '^#[0-9A-Fa-f]{6}$')
);

-- Workspace members table - MATCHES app/models/workspace_member.py EXACTLY
CREATE TABLE workspace_members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Foreign keys
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Role - STRATEGIC FIX: Uses workspace_role enum for member roles
    role workspace_role DEFAULT 'viewer' NOT NULL,
    
    -- Permissions and settings
    permissions JSONB DEFAULT '{}'::JSONB,
    settings JSONB DEFAULT '{}'::JSONB,
    meta_data JSONB DEFAULT '{}'::JSONB,
    
    -- Tracking
    added_by UUID REFERENCES users(id) ON DELETE SET NULL,
    deleted_by UUID REFERENCES users(id) ON DELETE SET NULL,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    
    -- Timestamps - STRATEGIC FIX: added_at not joined_at
    added_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    last_accessed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    -- Unique constraint
    CONSTRAINT workspace_members_unique UNIQUE(workspace_id, user_id)
);

-- Workspace invitations table - MATCHES app/models/workspace.py
CREATE TABLE workspace_invitations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Foreign keys
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    invited_by UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Invitation details
    email VARCHAR(255) NOT NULL,
    role workspace_role DEFAULT 'viewer' NOT NULL,
    token VARCHAR(255) UNIQUE NOT NULL,
    message TEXT,
    
    -- Status - STRATEGIC FIX: Uses invitation_status enum
    status invitation_status DEFAULT 'pending' NOT NULL,
    
    -- Timestamps
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    accepted_at TIMESTAMP WITH TIME ZONE,
    rejected_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    
    -- Metadata
    metadata JSONB DEFAULT '{}'::JSONB,
    
    -- Constraints
    CONSTRAINT workspace_invitations_email_check CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),
    CONSTRAINT workspace_invitations_expires_at_check CHECK (expires_at > created_at)
);

-- =============================================================================
-- INDEXES
-- =============================================================================

-- Workspaces indexes
CREATE INDEX idx_workspaces_created_by ON workspaces(created_by) WHERE deleted_at IS NULL;
CREATE INDEX idx_workspaces_updated_by ON workspaces(updated_by) WHERE deleted_at IS NULL;
CREATE INDEX idx_workspaces_deleted_by ON workspaces(deleted_by) WHERE deleted_at IS NOT NULL;
CREATE INDEX idx_workspaces_type ON workspaces(type) WHERE deleted_at IS NULL;
CREATE INDEX idx_workspaces_slug ON workspaces(slug) WHERE deleted_at IS NULL;
CREATE INDEX idx_workspaces_is_active ON workspaces(is_active) WHERE deleted_at IS NULL;
CREATE INDEX idx_workspaces_is_archived ON workspaces(is_archived) WHERE is_archived = TRUE;
CREATE INDEX idx_workspaces_created_at ON workspaces(created_at DESC);
CREATE INDEX idx_workspaces_updated_at ON workspaces(updated_at DESC);
CREATE INDEX idx_workspaces_deleted_at ON workspaces(deleted_at) WHERE deleted_at IS NOT NULL;

-- Full-text search index for workspaces
CREATE INDEX idx_workspaces_fulltext ON workspaces 
    USING gin(to_tsvector('english', 
        COALESCE(name, '') || ' ' || 
        COALESCE(description, '') || ' ' ||
        COALESCE(slug, '')
    )) WHERE deleted_at IS NULL;

-- Workspace members indexes
CREATE INDEX idx_workspace_members_workspace_id ON workspace_members(workspace_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_workspace_members_user_id ON workspace_members(user_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_workspace_members_role ON workspace_members(role) WHERE deleted_at IS NULL;
CREATE INDEX idx_workspace_members_added_by ON workspace_members(added_by) WHERE deleted_at IS NULL;
CREATE INDEX idx_workspace_members_added_at ON workspace_members(added_at DESC);
CREATE INDEX idx_workspace_members_last_accessed_at ON workspace_members(last_accessed_at DESC);
CREATE INDEX idx_workspace_members_is_active ON workspace_members(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_workspace_members_deleted_at ON workspace_members(deleted_at) WHERE deleted_at IS NOT NULL;

-- Composite indexes for common queries
CREATE INDEX idx_workspace_members_workspace_user ON workspace_members(workspace_id, user_id) 
    WHERE deleted_at IS NULL;

-- Workspace invitations indexes
CREATE INDEX idx_workspace_invitations_workspace_id ON workspace_invitations(workspace_id);
CREATE INDEX idx_workspace_invitations_email ON workspace_invitations(email);
CREATE INDEX idx_workspace_invitations_invited_by ON workspace_invitations(invited_by);
CREATE INDEX idx_workspace_invitations_token ON workspace_invitations(token);
CREATE INDEX idx_workspace_invitations_status ON workspace_invitations(status);
CREATE INDEX idx_workspace_invitations_expires_at ON workspace_invitations(expires_at);
CREATE INDEX idx_workspace_invitations_created_at ON workspace_invitations(created_at DESC);

-- Composite index for pending invitations
CREATE INDEX idx_workspace_invitations_workspace_email ON workspace_invitations(workspace_id, email)
    WHERE status = 'pending';

-- =============================================================================
-- TRIGGERS
-- =============================================================================

-- Function to update workspace updated_at timestamp
CREATE OR REPLACE FUNCTION update_workspace_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for workspace updates
CREATE TRIGGER workspace_update_timestamp
    BEFORE UPDATE ON workspaces
    FOR EACH ROW
    EXECUTE FUNCTION update_workspace_timestamp();

-- Function to update workspace_member updated_at timestamp
CREATE OR REPLACE FUNCTION update_workspace_member_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for workspace_member updates
CREATE TRIGGER workspace_member_update_timestamp
    BEFORE UPDATE ON workspace_members
    FOR EACH ROW
    EXECUTE FUNCTION update_workspace_member_timestamp();

-- Function to validate workspace member roles
CREATE OR REPLACE FUNCTION validate_workspace_member_role()
RETURNS TRIGGER AS $$
BEGIN
    -- Ensure at least one admin exists for the workspace
    IF TG_OP = 'DELETE' OR (TG_OP = 'UPDATE' AND NEW.role != 'admin') THEN
        IF NOT EXISTS (
            SELECT 1 FROM workspace_members
            WHERE workspace_id = COALESCE(NEW.workspace_id, OLD.workspace_id)
            AND role = 'admin'
            AND deleted_at IS NULL
            AND id != COALESCE(OLD.id, NEW.id)
        ) THEN
            -- Check if workspace creator exists as fallback
            IF NOT EXISTS (
                SELECT 1 FROM workspaces
                WHERE id = COALESCE(NEW.workspace_id, OLD.workspace_id)
                AND created_by IS NOT NULL
                AND deleted_at IS NULL
            ) THEN
                RAISE EXCEPTION 'Cannot remove last admin from workspace';
            END IF;
        END IF;
    END IF;
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Trigger to validate workspace member roles
CREATE TRIGGER workspace_member_role_validation
    BEFORE UPDATE OR DELETE ON workspace_members
    FOR EACH ROW
    EXECUTE FUNCTION validate_workspace_member_role();

-- =============================================================================
-- COMMENTS
-- =============================================================================

COMMENT ON TABLE workspaces IS 'Workspaces for organizing models and collaboration';
COMMENT ON COLUMN workspaces.created_by IS 'User who created the workspace (acts as workspace owner)';
COMMENT ON COLUMN workspaces.updated_by IS 'User who last updated the workspace';
COMMENT ON COLUMN workspaces.deleted_by IS 'User who deleted the workspace (soft delete)';
COMMENT ON COLUMN workspaces.type IS 'Workspace type: personal (private), team (shared), common (organization-wide)';
COMMENT ON COLUMN workspaces.slug IS 'URL-friendly unique identifier';
COMMENT ON COLUMN workspaces.settings IS 'Workspace-specific settings';
COMMENT ON COLUMN workspaces.meta_data IS 'Additional metadata';

COMMENT ON TABLE workspace_members IS 'User membership and permissions in workspaces';
COMMENT ON COLUMN workspace_members.role IS 'Member role: viewer, editor, publisher, admin';
COMMENT ON COLUMN workspace_members.added_by IS 'User who added this member';
COMMENT ON COLUMN workspace_members.deleted_by IS 'User who removed this member';
COMMENT ON COLUMN workspace_members.added_at IS 'When member was added to workspace';

COMMENT ON TABLE workspace_invitations IS 'Pending invitations to join workspaces';
COMMENT ON COLUMN workspace_invitations.status IS 'Invitation status: pending, accepted, rejected, expired';

-- Logging
DO $$
BEGIN
    RAISE NOTICE '✅ Workspace schema created successfully';
    RAISE NOTICE '✅ Using created_by/updated_by/deleted_by pattern (not owner_id)';
    RAISE NOTICE '✅ Column names match SQLAlchemy models exactly';
    RAISE NOTICE '✅ Enum types: workspace_type, user_role, invitation_status';
    RAISE NOTICE '✅ Indexes created for performance';
    RAISE NOTICE '✅ Triggers created for data integrity';
END $$;