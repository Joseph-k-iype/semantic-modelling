-- database/postgres/init/01-init-db.sql
-- MUST RUN FIRST - Creates extensions, enums, and base functions
-- This file goes in database/postgres/init/ directory

BEGIN;

-- ============================================================================
-- EXTENSIONS
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gist";

-- ============================================================================
-- ENUMS - Create ALL enums before any schema files
-- ============================================================================

-- User role enum
DO $$ BEGIN
    CREATE TYPE user_role AS ENUM ('user', 'admin', 'superuser');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Workspace type enum
DO $$ BEGIN
    CREATE TYPE workspace_type AS ENUM ('personal', 'team', 'organization');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Workspace role enum
DO $$ BEGIN
    CREATE TYPE workspace_role AS ENUM ('owner', 'admin', 'editor', 'viewer');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Invitation status enum
DO $$ BEGIN
    CREATE TYPE invitation_status AS ENUM ('pending', 'accepted', 'rejected', 'expired');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Model type enum
DO $$ BEGIN
    CREATE TYPE model_type AS ENUM (
        'ER',
        'UML_CLASS',
        'UML_SEQUENCE',
        'UML_ACTIVITY',
        'UML_STATE',
        'UML_COMPONENT',
        'UML_DEPLOYMENT',
        'UML_PACKAGE',
        'BPMN',
        'MIXED'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Diagram notation enum
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

-- Layout type enum
DO $$ BEGIN
    CREATE TYPE layout_type AS ENUM (
        'manual',
        'layered',
        'force',
        'hierarchical',
        'radial',
        'circular'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Version type enum
DO $$ BEGIN
    CREATE TYPE version_type AS ENUM (
        'major',
        'minor',
        'patch',
        'snapshot'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Publish status enum
DO $$ BEGIN
    CREATE TYPE publish_status AS ENUM (
        'DRAFT',
        'PENDING_REVIEW',
        'IN_REVIEW',
        'APPROVED',
        'REJECTED',
        'PUBLISHED',
        'ARCHIVED'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Validation status enum
DO $$ BEGIN
    CREATE TYPE validation_status AS ENUM (
        'PENDING',
        'VALIDATING',
        'VALID',
        'INVALID',
        'ERROR'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Entity type enum
DO $$ BEGIN
    CREATE TYPE entity_type AS ENUM (
        'workspace',
        'folder',
        'model',
        'diagram',
        'layout',
        'version',
        'publish_request',
        'comment'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- ============================================================================
-- HELPER FUNCTIONS - Base functions used across schemas
-- ============================================================================

-- Function to generate a slug from text
CREATE OR REPLACE FUNCTION generate_slug(text_input TEXT)
RETURNS TEXT AS $$
DECLARE
    slug TEXT;
BEGIN
    slug := LOWER(text_input);
    slug := REGEXP_REPLACE(slug, '[^a-z0-9]+', '-', 'g');
    slug := TRIM(BOTH '-' FROM slug);
    slug := SUBSTRING(slug, 1, 100);
    RETURN slug;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- LOGGING
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '============================================';
    RAISE NOTICE 'Database initialization complete';
    RAISE NOTICE '============================================';
    RAISE NOTICE '✓ Extensions created: uuid-ossp, pg_trgm, btree_gist';
    RAISE NOTICE '✓ Enums created: 10 types';
    RAISE NOTICE '✓ Helper functions created';
    RAISE NOTICE '============================================';
    RAISE NOTICE 'Ready for schema files';
    RAISE NOTICE '============================================';
END $$;

COMMIT;