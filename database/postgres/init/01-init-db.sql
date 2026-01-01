-- database/postgres/init/01-init-db.sql
-- PostgreSQL Initialization Script for Enterprise Modeling Platform
-- This script sets up extensions, custom types, and utility functions
-- Prerequisites: modeling user and modeling_platform database must already exist (created by 00-create-user-and-db.sh)

-- Connect to modeling_platform database
\c modeling_platform

-- Enable required PostgreSQL extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gist";

-- Create custom enum types
DO $$ BEGIN
    CREATE TYPE user_role AS ENUM ('ADMIN', 'USER');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE workspace_role AS ENUM ('VIEWER', 'EDITOR', 'PUBLISHER', 'ADMIN');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE workspace_type AS ENUM ('PERSONAL', 'TEAM', 'COMMON');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE model_type AS ENUM (
        'ER',
        'UML',
        'BPMN',
        'CUSTOM',
        'MIXED'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE model_status AS ENUM (
        'DRAFT',
        'IN_REVIEW',
        'APPROVED',
        'PUBLISHED',
        'ARCHIVED'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE diagram_notation AS ENUM (
        'ER',
        'UML_CLASS',
        'UML_SEQUENCE',
        'UML_ACTIVITY',
        'UML_STATE',
        'UML_COMPONENT',
        'UML_DEPLOYMENT',
        'UML_PACKAGE',
        'BPMN'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE layout_type AS ENUM (
        'MANUAL',
        'LAYERED',
        'FORCE_DIRECTED',
        'BPMN_SWIMLANE',
        'UML_SEQUENCE',
        'STATE_MACHINE',
        'HIERARCHICAL'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE publish_status AS ENUM (
        'DRAFT',
        'PENDING_REVIEW',
        'APPROVED',
        'REJECTED',
        'PUBLISHED',
        'ARCHIVED'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE version_type AS ENUM ('MAJOR', 'MINOR', 'PATCH');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE audit_action AS ENUM (
        'CREATE',
        'UPDATE',
        'DELETE',
        'PUBLISH',
        'ARCHIVE',
        'RESTORE',
        'SHARE',
        'PERMISSION_CHANGE'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE entity_type AS ENUM (
        'USER',
        'WORKSPACE',
        'FOLDER',
        'MODEL',
        'DIAGRAM',
        'LAYOUT',
        'VERSION',
        'PUBLISH_WORKFLOW',
        'COMMENT'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Utility function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Utility function to prevent updates on immutable records
CREATE OR REPLACE FUNCTION prevent_update_immutable()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Cannot update immutable record';
END;
$$ LANGUAGE plpgsql;

-- Function to validate JSON schema
CREATE OR REPLACE FUNCTION validate_jsonb_keys(data JSONB, required_keys TEXT[])
RETURNS BOOLEAN AS $$
DECLARE
    key TEXT;
BEGIN
    FOREACH key IN ARRAY required_keys
    LOOP
        IF NOT (data ? key) THEN
            RETURN FALSE;
        END IF;
    END LOOP;
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Function to generate semantic version string
CREATE OR REPLACE FUNCTION generate_version_string(major INT, minor INT, patch INT)
RETURNS VARCHAR(20) AS $$
BEGIN
    RETURN CONCAT(major, '.', minor, '.', patch);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Function to soft delete with cascade
CREATE OR REPLACE FUNCTION soft_delete_cascade()
RETURNS TRIGGER AS $$
BEGIN
    NEW.deleted_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Grant necessary permissions to modeling user
GRANT ALL PRIVILEGES ON SCHEMA public TO modeling;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO modeling;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO modeling;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO modeling;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO modeling;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO modeling;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT EXECUTE ON FUNCTIONS TO modeling;

-- Logging
DO $$
BEGIN
    RAISE NOTICE '============================================';
    RAISE NOTICE 'Database Initialization Complete';
    RAISE NOTICE '============================================';
    RAISE NOTICE '✓ Database: modeling_platform';
    RAISE NOTICE '✓ Extensions: uuid-ossp, pgcrypto, pg_trgm, btree_gist';
    RAISE NOTICE '✓ Custom types: Created';
    RAISE NOTICE '✓ Utility functions: Created';
    RAISE NOTICE '✓ Permissions: Granted to modeling user';
    RAISE NOTICE '============================================';
END $$;