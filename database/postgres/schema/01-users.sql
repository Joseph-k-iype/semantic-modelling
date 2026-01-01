-- database/postgres/schema/01-users.sql
-- Users table and related structures
-- FIXED: Added missing updated_by column

-- Drop existing table if exists (for clean reinstall)
DROP TABLE IF EXISTS user_sessions CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    password_hash VARCHAR(255) NOT NULL,
    role user_role DEFAULT 'USER' NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    is_verified BOOLEAN DEFAULT FALSE NOT NULL,
    email_verified_at TIMESTAMP WITH TIME ZONE,
    avatar_url TEXT,
    preferences JSONB DEFAULT '{}'::JSONB,
    settings JSONB DEFAULT '{}'::JSONB,
    last_login_at TIMESTAMP WITH TIME ZONE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    
    -- CRITICAL FIX: Added missing updated_by column to match other tables
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    updated_by UUID REFERENCES users(id) ON DELETE SET NULL,
    
    -- Constraints
    CONSTRAINT users_email_check CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),
    CONSTRAINT users_username_check CHECK (username ~* '^[A-Za-z0-9_-]{3,100}$'),
    CONSTRAINT users_password_hash_check CHECK (LENGTH(password_hash) >= 60)
);

-- User sessions table for JWT token management
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_jti VARCHAR(255) UNIQUE NOT NULL,
    refresh_token_jti VARCHAR(255) UNIQUE,
    ip_address INET,
    user_agent TEXT,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    last_activity_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    
    -- Constraints
    CONSTRAINT user_sessions_expires_at_check CHECK (expires_at > created_at)
);

-- Indexes for users table
CREATE INDEX idx_users_email ON users(email) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_username ON users(username) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_role ON users(role) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_is_active ON users(is_active) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_created_at ON users(created_at DESC);
CREATE INDEX idx_users_deleted_at ON users(deleted_at) WHERE deleted_at IS NOT NULL;
CREATE INDEX idx_users_created_by ON users(created_by) WHERE created_by IS NOT NULL;
CREATE INDEX idx_users_updated_by ON users(updated_by) WHERE updated_by IS NOT NULL;

-- Indexes for user_sessions table
CREATE INDEX idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_user_sessions_token_jti ON user_sessions(token_jti);
CREATE INDEX idx_user_sessions_is_active ON user_sessions(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_user_sessions_expires_at ON user_sessions(expires_at);

-- Trigger for updated_at
CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Function to track user updates (sets updated_by)
CREATE OR REPLACE FUNCTION track_user_updates()
RETURNS TRIGGER AS $$
BEGIN
    -- On INSERT, set created_by to the user being created (self-reference)
    IF TG_OP = 'INSERT' THEN
        NEW.created_by := NEW.id;
        NEW.updated_by := NEW.id;
    END IF;
    
    -- On UPDATE, only update updated_by if it's not already set
    IF TG_OP = 'UPDATE' THEN
        IF NEW.updated_by IS NULL THEN
            NEW.updated_by := NEW.id;
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to track user updates
CREATE TRIGGER track_user_updates_trigger
    BEFORE INSERT OR UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION track_user_updates();

-- Insert system user for operations without a logged-in user
INSERT INTO users (
    id,
    email,
    username,
    full_name,
    password_hash,
    role,
    is_active,
    is_verified
) VALUES (
    '00000000-0000-0000-0000-000000000000'::UUID,
    'system@enterprise-modeling.com',
    'system',
    'System User',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeZD7LZZwIL9DkW7e', -- password: system (not used)
    'ADMIN',
    TRUE,
    TRUE
) ON CONFLICT (id) DO NOTHING;

-- Logging
DO $$
BEGIN
    RAISE NOTICE 'Users schema created successfully';
    RAISE NOTICE '✓ Added created_by and updated_by columns';
    RAISE NOTICE '✓ Created system user: 00000000-0000-0000-0000-000000000000';
END $$;