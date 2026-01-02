-- database/postgres/init/01-init-db.sql
-- PostgreSQL Initialization Script for Enterprise Modeling Platform
-- STRATEGIC FIX: Correct enum values matching Python models exactly

-- Connect to modeling_platform database
\c modeling_platform

-- Enable required PostgreSQL extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gist";

-- =============================================================================
-- ENUM TYPES - STRATEGIC FIX: All values in lowercase to match Python enums
-- =============================================================================

-- User role enum - MATCHES app/models/user.py
-- Used for users.role
DO $ BEGIN
    CREATE TYPE user_role AS ENUM ('ADMIN', 'USER');
EXCEPTION
    WHEN duplicate_object THEN null;
END $;

-- Workspace member role enum - MATCHES app/models/workspace_member.py WorkspaceMemberRole
-- Used for workspace_members.role
-- STRATEGIC FIX: lowercase values matching Python enum
DO $ BEGIN
    CREATE TYPE workspace_role AS ENUM ('viewer', 'editor', 'publisher', 'admin');
EXCEPTION
    WHEN duplicate_object THEN null;
END $;

-- Workspace type enum - MATCHES app/models/workspace.py WorkspaceType
DO $$ BEGIN
    CREATE TYPE workspace_type AS ENUM ('personal', 'team', 'common');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Invitation status enum - MATCHES app/models/workspace.py InvitationStatus
DO $$ BEGIN
    CREATE TYPE invitation_status AS ENUM ('pending', 'accepted', 'rejected', 'expired');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Model type enum - MATCHES app/models/model.py ModelType
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

-- Model status enum - MATCHES app/models/model.py ModelStatus
DO $$ BEGIN
    CREATE TYPE model_status AS ENUM (
        'draft',
        'in_review',
        'published',
        'archived'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Diagram notation enum - MATCHES app/models/diagram.py DiagramNotation
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

-- Layout engine enum - MATCHES app/models/layout.py LayoutEngine
DO $$ BEGIN
    CREATE TYPE layout_engine AS ENUM (
        'manual',
        'layered',
        'force_directed',
        'hierarchical',
        'circular',
        'orthogonal',
        'tree'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Publish status enum - MATCHES app/models/publish_workflow.py PublishWorkflowStatus
DO $$ BEGIN
    CREATE TYPE publish_status AS ENUM (
        'PENDING',
        'APPROVED',
        'REJECTED',
        'CANCELLED'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Version type enum - MATCHES app/models/version.py VersionType
DO $$ BEGIN
    CREATE TYPE version_type AS ENUM ('major', 'minor', 'patch');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Entity type enum for audit logs
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

-- Audit action enum
DO $$ BEGIN
    CREATE TYPE audit_action AS ENUM (
        'CREATE',
        'UPDATE',
        'DELETE',
        'RESTORE',
        'PUBLISH',
        'UNPUBLISH',
        'SHARE',
        'UNSHARE'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Validation severity enum
DO $$ BEGIN
    CREATE TYPE validation_severity AS ENUM (
        'ERROR',
        'WARNING',
        'INFO'
    );
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
    -- Convert to lowercase, replace spaces with hyphens, remove special characters
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
    RETURN prefix || '_' || REPLACE(uuid_generate_v4()::TEXT, '-', '');
END;
$$ LANGUAGE plpgsql VOLATILE;

-- Logging
DO $$
BEGIN
    RAISE NOTICE '✅ PostgreSQL extensions enabled';
    RAISE NOTICE '✅ Custom enum types created with correct lowercase values';
    RAISE NOTICE '✅ Utility functions created';
    RAISE NOTICE '✅ Database initialization complete';
    RAISE NOTICE '';
    RAISE NOTICE 'Created enum types:';
    RAISE NOTICE '  - user_role (ADMIN, USER) for users table';
    RAISE NOTICE '  - workspace_role (viewer, editor, publisher, admin) for workspace members';
    RAISE NOTICE '  - workspace_type (personal, team, common)';
    RAISE NOTICE '  - invitation_status (pending, accepted, rejected, expired)';
    RAISE NOTICE '  - model_type (ER, UML_*, BPMN, MIXED)';
    RAISE NOTICE '  - model_status (draft, in_review, published, archived)';
    RAISE NOTICE '  - diagram_notation (ER, UML_*, BPMN)';
    RAISE NOTICE '  - layout_engine (manual, layered, force_directed, etc.)';
    RAISE NOTICE '  - publish_status (PENDING, APPROVED, REJECTED, CANCELLED)';
    RAISE NOTICE '  - version_type (major, minor, patch)';
    RAISE NOTICE '  - entity_type (for audit logs)';
    RAISE NOTICE '  - audit_action (for audit logs)';
    RAISE NOTICE '  - validation_severity (ERROR, WARNING, INFO)';
END $;