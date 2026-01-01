-- database/postgres/schema/02-workspaces.sql
-- Workspaces and workspace membership tables

-- Drop existing tables if exist (for clean reinstall)
DROP TABLE IF EXISTS workspace_members CASCADE;
DROP TABLE IF EXISTS workspace_invitations CASCADE;
DROP TABLE IF EXISTS workspaces CASCADE;

-- Workspaces table
CREATE TABLE workspaces (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    type workspace_type DEFAULT 'TEAM' NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    owner_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    settings JSONB DEFAULT '{}'::JSONB,
    metadata JSONB DEFAULT '{}'::JSONB,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    deleted_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    
    -- Constraints
    CONSTRAINT workspaces_name_check CHECK (LENGTH(TRIM(name)) >= 1),
    CONSTRAINT workspaces_slug_check CHECK (slug ~* '^[a-z0-9-]{3,100}$')
);

-- Workspace members table (junction table with roles)
CREATE TABLE workspace_members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role workspace_role DEFAULT 'VIEWER' NOT NULL,
    permissions JSONB DEFAULT '{}'::JSONB,
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    invited_by UUID REFERENCES users(id) ON DELETE SET NULL,
    last_accessed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    
    -- Unique constraint: one user can only have one role per workspace
    CONSTRAINT workspace_members_unique UNIQUE(workspace_id, user_id)
);

-- Workspace invitations table
CREATE TABLE workspace_invitations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    role workspace_role DEFAULT 'VIEWER' NOT NULL,
    invited_by UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    accepted_at TIMESTAMP WITH TIME ZONE,
    rejected_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    
    -- Constraints
    CONSTRAINT workspace_invitations_email_check CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),
    CONSTRAINT workspace_invitations_expires_at_check CHECK (expires_at > created_at),
    CONSTRAINT workspace_invitations_status_check CHECK (
        (accepted_at IS NULL AND rejected_at IS NULL) OR
        (accepted_at IS NOT NULL AND rejected_at IS NULL) OR
        (accepted_at IS NULL AND rejected_at IS NOT NULL)
    )
);

-- Indexes for workspaces table
CREATE INDEX idx_workspaces_owner_id ON workspaces(owner_id);
CREATE INDEX idx_workspaces_type ON workspaces(type) WHERE deleted_at IS NULL;
CREATE INDEX idx_workspaces_slug ON workspaces(slug) WHERE deleted_at IS NULL;
CREATE INDEX idx_workspaces_is_active ON workspaces(is_active) WHERE deleted_at IS NULL;
CREATE INDEX idx_workspaces_created_at ON workspaces(created_at DESC);
CREATE INDEX idx_workspaces_deleted_at ON workspaces(deleted_at) WHERE deleted_at IS NOT NULL;

-- Full-text search index
CREATE INDEX idx_workspaces_fulltext ON workspaces 
    USING gin(to_tsvector('english', 
        COALESCE(name, '') || ' ' || 
        COALESCE(description, '') || ' ' ||
        COALESCE(slug, '')
    )) WHERE deleted_at IS NULL;

-- Indexes for workspace_members table
CREATE INDEX idx_workspace_members_workspace_id ON workspace_members(workspace_id);
CREATE INDEX idx_workspace_members_user_id ON workspace_members(user_id);
CREATE INDEX idx_workspace_members_role ON workspace_members(role);
CREATE INDEX idx_workspace_members_joined_at ON workspace_members(joined_at DESC);
CREATE INDEX idx_workspace_members_last_accessed_at ON workspace_members(last_accessed_at DESC);

-- Indexes for workspace_invitations table
CREATE INDEX idx_workspace_invitations_workspace_id ON workspace_invitations(workspace_id);
CREATE INDEX idx_workspace_invitations_email ON workspace_invitations(email);
CREATE INDEX idx_workspace_invitations_token ON workspace_invitations(token);
CREATE INDEX idx_workspace_invitations_expires_at ON workspace_invitations(expires_at);
CREATE INDEX idx_workspace_invitations_invited_by ON workspace_invitations(invited_by);

-- Trigger to update updated_at timestamp
CREATE TRIGGER update_workspaces_updated_at
    BEFORE UPDATE ON workspaces
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_workspace_members_updated_at
    BEFORE UPDATE ON workspace_members
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger to automatically add owner as ADMIN member
CREATE OR REPLACE FUNCTION add_owner_as_admin()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO workspace_members (workspace_id, user_id, role)
    VALUES (NEW.id, NEW.owner_id, 'ADMIN')
    ON CONFLICT (workspace_id, user_id) 
    DO UPDATE SET role = 'ADMIN';
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER workspace_add_owner_as_admin
    AFTER INSERT ON workspaces
    FOR EACH ROW
    EXECUTE FUNCTION add_owner_as_admin();

-- Trigger to create personal workspace for new users
CREATE OR REPLACE FUNCTION create_personal_workspace()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO workspaces (name, slug, type, owner_id)
    VALUES (
        NEW.username || '''s Personal Workspace',
        NEW.username || '-personal',
        'PERSONAL',
        NEW.id
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER user_create_personal_workspace
    AFTER INSERT ON users
    FOR EACH ROW
    EXECUTE FUNCTION create_personal_workspace();

-- Function to check workspace permissions
CREATE OR REPLACE FUNCTION has_workspace_permission(
    p_user_id UUID,
    p_workspace_id UUID,
    p_required_role workspace_role
)
RETURNS BOOLEAN AS $$
DECLARE
    user_role workspace_role;
    role_hierarchy INTEGER;
    required_hierarchy INTEGER;
BEGIN
    -- Get user's role in workspace
    SELECT role INTO user_role
    FROM workspace_members
    WHERE workspace_id = p_workspace_id 
    AND user_id = p_user_id;
    
    -- If user is not a member, return false
    IF user_role IS NULL THEN
        RETURN FALSE;
    END IF;
    
    -- Define role hierarchy (higher number = more permissions)
    role_hierarchy := CASE user_role
        WHEN 'ADMIN' THEN 4
        WHEN 'PUBLISHER' THEN 3
        WHEN 'EDITOR' THEN 2
        WHEN 'VIEWER' THEN 1
        ELSE 0
    END;
    
    required_hierarchy := CASE p_required_role
        WHEN 'ADMIN' THEN 4
        WHEN 'PUBLISHER' THEN 3
        WHEN 'EDITOR' THEN 2
        WHEN 'VIEWER' THEN 1
        ELSE 0
    END;
    
    RETURN role_hierarchy >= required_hierarchy;
END;
$$ LANGUAGE plpgsql STABLE;

-- Function to clean expired invitations
CREATE OR REPLACE FUNCTION cleanup_expired_invitations()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM workspace_invitations 
    WHERE expires_at < NOW() 
    AND accepted_at IS NULL 
    AND rejected_at IS NULL;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Logging
DO $$
BEGIN
    RAISE NOTICE 'Workspaces schema created successfully';
END $$;