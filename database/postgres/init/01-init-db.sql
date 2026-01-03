-- database/postgres/init/01-init-db.sql
-- PostgreSQL Initialization Script - COMPLETE FIX
-- CRITICAL: ENUM names must match schema files exactly

-- Connect to modeling_platform database
\c modeling_platform

-- Enable required PostgreSQL extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gist";

-- =============================================================================
-- ENUM TYPES - CRITICAL: Names must match schema files
-- =============================================================================

-- User role enum
DO $$ BEGIN
    CREATE TYPE user_role AS ENUM ('ADMIN', 'USER');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Workspace member role enum - Name: workspace_role
DO $$ BEGIN
    CREATE TYPE workspace_role AS ENUM ('viewer', 'editor', 'publisher', 'admin');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Workspace type enum - Name: workspace_type
DO $$ BEGIN
    CREATE TYPE workspace_type AS ENUM ('personal', 'team', 'common');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Invitation status enum - Name: invitation_status
DO $$ BEGIN
    CREATE TYPE invitation_status AS ENUM ('pending', 'accepted', 'rejected', 'expired');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Diagram notation enum - Name: diagram_notation (NOT diagram_type!)
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

-- Layout type enum - Name: layout_type (NOT layout_engine!)
DO $$ BEGIN
    CREATE TYPE layout_type AS ENUM (
        'MANUAL',
        'LAYERED',
        'FORCE_DIRECTED',
        'BPMN_SWIMLANE',
        'UML_SEQUENCE',
        'STATE_MACHINE'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Version type enum - Name: version_type
DO $$ BEGIN
    CREATE TYPE version_type AS ENUM ('MAJOR', 'MINOR', 'PATCH', 'SNAPSHOT');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Publish status enum - Name: publish_status
DO $$ BEGIN
    CREATE TYPE publish_status AS ENUM ('DRAFT', 'SUBMITTED', 'IN_REVIEW', 'APPROVED', 'REJECTED', 'PUBLISHED');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Entity type enum - Name: entity_type (for comments and audit logs)
DO $$ BEGIN
    CREATE TYPE entity_type AS ENUM (
        'MODEL',
        'DIAGRAM',
        'LAYOUT',
        'VERSION',
        'WORKSPACE',
        'FOLDER',
        'COMMENT',
        'USER'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Audit action enum - Name: audit_action
DO $$ BEGIN
    CREATE TYPE audit_action AS ENUM (
        'CREATE',
        'UPDATE',
        'DELETE',
        'PUBLISH',
        'APPROVE',
        'REJECT',
        'COMMENT',
        'SHARE',
        'EXPORT'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Validation severity enum - Name: validation_severity
DO $$ BEGIN
    CREATE TYPE validation_severity AS ENUM ('ERROR', 'WARNING', 'INFO');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- =============================================================================
-- UTILITY FUNCTIONS
-- =============================================================================

-- Function to generate slug from text
CREATE OR REPLACE FUNCTION generate_slug(text_input TEXT)
RETURNS TEXT AS $$
DECLARE
    slug TEXT;
BEGIN
    slug := LOWER(text_input);
    slug := REGEXP_REPLACE(slug, '[^a-z0-9\s-]', '', 'g');
    slug := REGEXP_REPLACE(slug, '\s+', '-', 'g');
    slug := REGEXP_REPLACE(slug, '-+', '-', 'g');
    slug := TRIM(BOTH '-' FROM slug);
    
    RETURN slug;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Function to update timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Function to generate unique graph ID
CREATE OR REPLACE FUNCTION generate_graph_id(prefix TEXT DEFAULT 'graph')
RETURNS TEXT AS $$
BEGIN
    RETURN prefix || '_' || REPLACE(gen_random_uuid()::TEXT, '-', '');
END;
$$ LANGUAGE plpgsql VOLATILE;

-- =============================================================================
-- LOGGING
-- =============================================================================

DO $$
BEGIN
    RAISE NOTICE '═══════════════════════════════════════════════════';
    RAISE NOTICE '✅ PostgreSQL Initialization Complete';
    RAISE NOTICE '═══════════════════════════════════════════════════';
    RAISE NOTICE '';
    RAISE NOTICE 'Extensions Enabled:';
    RAISE NOTICE '  ✓ uuid-ossp (UUID generation)';
    RAISE NOTICE '  ✓ pgcrypto (cryptographic functions)';
    RAISE NOTICE '  ✓ pg_trgm (trigram matching for fuzzy search)';
    RAISE NOTICE '  ✓ btree_gist (spatial indexing)';
    RAISE NOTICE '';
    RAISE NOTICE 'ENUM Types Created:';
    RAISE NOTICE '  ✓ user_role';
    RAISE NOTICE '  ✓ workspace_role';
    RAISE NOTICE '  ✓ workspace_type';
    RAISE NOTICE '  ✓ invitation_status';
    RAISE NOTICE '  ✓ diagram_notation';
    RAISE NOTICE '  ✓ layout_type';
    RAISE NOTICE '  ✓ version_type';
    RAISE NOTICE '  ✓ publish_status';
    RAISE NOTICE '  ✓ entity_type';
    RAISE NOTICE '  ✓ audit_action';
    RAISE NOTICE '  ✓ validation_severity';
    RAISE NOTICE '';
    RAISE NOTICE 'Utility Functions Created:';
    RAISE NOTICE '  ✓ generate_slug()';
    RAISE NOTICE '  ✓ update_updated_at_column()';
    RAISE NOTICE '  ✓ generate_graph_id()';
    RAISE NOTICE '';
    RAISE NOTICE '═══════════════════════════════════════════════════';
END $$;