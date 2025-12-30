-- database/postgres/init/01-init-db.sql
-- PostgreSQL Database Initialization Script - FIXED
-- Creates the correct database, users, and grants permissions

\echo '========================================================================'
\echo 'PostgreSQL Initialization Started'
\echo 'Enterprise Modeling Platform Database Setup'
\echo '========================================================================'

-- ============================================================================
-- STEP 1: Create modeling user (if it doesn't exist)
-- ============================================================================
\echo ''
\echo 'Step 1: Creating modeling user...'

DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_user WHERE usename = 'modeling') THEN
        CREATE USER modeling WITH PASSWORD 'modeling_dev';
        RAISE NOTICE 'Created user: modeling';
    ELSE
        RAISE NOTICE 'User modeling already exists';
    END IF;
END $$;

-- ============================================================================
-- STEP 2: Create modeling_platform database (PRIMARY DATABASE)
-- ============================================================================
\echo ''
\echo 'Step 2: Creating modeling_platform database...'

SELECT 'CREATE DATABASE modeling_platform'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'modeling_platform')\gexec

\echo 'Database modeling_platform created or already exists'

-- ============================================================================
-- STEP 3: Grant privileges on modeling_platform database
-- ============================================================================
\echo ''
\echo 'Step 3: Granting privileges on modeling_platform...'

GRANT ALL PRIVILEGES ON DATABASE modeling_platform TO modeling;

-- ============================================================================
-- STEP 4: Connect to modeling_platform and set up extensions and schema
-- ============================================================================
\echo ''
\echo 'Step 4: Setting up modeling_platform database...'
\c modeling_platform

-- Create essential extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- Trigram similarity for text search
CREATE EXTENSION IF NOT EXISTS "btree_gin";  -- Better indexing
CREATE EXTENSION IF NOT EXISTS "hstore";  -- Key-value store

\echo 'Extensions created'

-- Grant schema permissions
GRANT ALL PRIVILEGES ON SCHEMA public TO modeling;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO modeling;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO modeling;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO modeling;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO modeling;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO modeling;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO modeling;

-- Set database owner
ALTER DATABASE modeling_platform OWNER TO modeling;

\echo 'Permissions granted'

-- ============================================================================
-- STEP 5: Create helper function for updated_at timestamps
-- ============================================================================
\echo ''
\echo 'Step 5: Creating helper functions...'

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

\echo 'Helper functions created'

-- ============================================================================
-- STEP 6: Create enum types for the application
-- ============================================================================
\echo ''
\echo 'Step 6: Creating enum types...'

-- Workspace types
DO $$ BEGIN
    CREATE TYPE workspace_type AS ENUM ('personal', 'team', 'common');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- User roles
DO $$ BEGIN
    CREATE TYPE user_role AS ENUM ('viewer', 'editor', 'publisher', 'admin');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Model types
DO $$ BEGIN
    CREATE TYPE model_type AS ENUM ('ER', 'UML', 'BPMN', 'CUSTOM');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Model status
DO $$ BEGIN
    CREATE TYPE model_status AS ENUM ('draft', 'in_review', 'published', 'archived');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Publish request status
DO $$ BEGIN
    CREATE TYPE publish_status AS ENUM ('pending', 'approved', 'rejected', 'cancelled');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

\echo 'Enum types created'

-- ============================================================================
-- SUMMARY
-- ============================================================================
\echo ''
\echo '========================================================================'
\echo '✅ PostgreSQL Initialization Complete!'
\echo '========================================================================'
\echo ''
\echo 'Database Setup Summary:'
\echo '  - Database: modeling_platform'
\echo '  - User: modeling'
\echo '  - Password: modeling_dev'
\echo '  - Extensions: uuid-ossp, pg_trgm, btree_gin, hstore'
\echo '  - Functions: update_updated_at_column()'
\echo '  - Enums: workspace_type, user_role, model_type, model_status, publish_status'
\echo ''
\echo 'Next Steps:'
\echo '  1. Apply schema files from database/postgres/schema/'
\echo '  2. Run init_database.py to create test users and data'
\echo '  3. Start the backend service'
\echo ''
\echo '========================================================================'