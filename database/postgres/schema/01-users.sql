-- database/postgres/schema/01-users.sql
-- Users table and related structures

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

-- Full-text search index
CREATE INDEX idx_users_fulltext ON users 
    USING gin(to_tsvector('english', 
        COALESCE(full_name, '') || ' ' || 
        COALESCE(username, '') || ' ' || 
        COALESCE(email, '')
    )) WHERE deleted_at IS NULL;

-- Indexes for user_sessions table
CREATE INDEX idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_user_sessions_token_jti ON user_sessions(token_jti) WHERE is_active = TRUE;
CREATE INDEX idx_user_sessions_refresh_token_jti ON user_sessions(refresh_token_jti) WHERE is_active = TRUE;
CREATE INDEX idx_user_sessions_expires_at ON user_sessions(expires_at) WHERE is_active = TRUE;
CREATE INDEX idx_user_sessions_last_activity_at ON user_sessions(last_activity_at DESC);

-- Trigger to update updated_at timestamp
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger to update last_activity_at on user_sessions
CREATE OR REPLACE FUNCTION update_session_activity()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_activity_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_user_sessions_activity
    BEFORE UPDATE ON user_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_session_activity();

-- Function to clean expired sessions
CREATE OR REPLACE FUNCTION cleanup_expired_sessions()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM user_sessions 
    WHERE expires_at < NOW() 
    OR (is_active = FALSE AND last_activity_at < NOW() - INTERVAL '30 days');
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Create default admin user (password: Admin@123)
-- Password hash is bcrypt hash of "Admin@123"
INSERT INTO users (
    id,
    email,
    username,
    full_name,
    password_hash,
    role,
    is_active,
    is_verified,
    email_verified_at
) VALUES (
    uuid_generate_v4(),
    'admin@enterprise-modeling.com',
    'admin',
    'System Administrator',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyGNzKqfNwXu',
    'ADMIN',
    TRUE,
    TRUE,
    NOW()
) ON CONFLICT (email) DO NOTHING;

-- Logging
DO $$
BEGIN
    RAISE NOTICE 'Users schema created successfully';
END $$;