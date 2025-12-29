-- database/postgres/init/01-init-db.sql
-- PostgreSQL Database Initialization Script
-- Creates databases, users, and grants permissions

\echo '================================================'
\echo 'PostgreSQL Initialization Started'
\echo '================================================'

-- Create modeling user (if it doesn't exist)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_user WHERE usename = 'modeling') THEN
        CREATE USER modeling WITH PASSWORD 'modeling_dev';
        RAISE NOTICE 'Created user: modeling';
    ELSE
        RAISE NOTICE 'User modeling already exists';
    END IF;
END $$;

-- Create modeling database
SELECT 'CREATE DATABASE modeling'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'modeling')\gexec

-- Create modeling_platform database
SELECT 'CREATE DATABASE modeling_platform'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'modeling_platform')\gexec

-- Grant privileges on databases to modeling user
GRANT ALL PRIVILEGES ON DATABASE modeling TO modeling;
GRANT ALL PRIVILEGES ON DATABASE modeling_platform TO modeling;

-- Connect to modeling database and set up schema
\c modeling

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

GRANT ALL PRIVILEGES ON SCHEMA public TO modeling;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO modeling;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO modeling;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO modeling;

ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO modeling;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO modeling;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO modeling;

ALTER DATABASE modeling OWNER TO modeling;

-- Connect to modeling_platform database and set up schema
\c modeling_platform

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

GRANT ALL PRIVILEGES ON SCHEMA public TO modeling;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO modeling;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO modeling;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO modeling;

ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO modeling;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO modeling;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO modeling;

ALTER DATABASE modeling_platform OWNER TO modeling;

\echo '================================================'
\echo 'PostgreSQL Initialization Complete!'
\echo 'Databases: modeling, modeling_platform'
\echo 'User: modeling (password: modeling_dev)'
\echo '================================================'