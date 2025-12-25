-- Create both possible database names
CREATE DATABASE modeling;
CREATE DATABASE modeling_platform;

-- Initialize modeling database
\c modeling;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE SCHEMA IF NOT EXISTS public;

-- Create and configure modeling user
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_user WHERE usename = 'modeling') THEN
        CREATE USER modeling WITH PASSWORD 'modeling_dev';
    END IF;
END $$;

GRANT ALL PRIVILEGES ON DATABASE modeling TO modeling;
GRANT ALL PRIVILEGES ON SCHEMA public TO modeling;
ALTER DATABASE modeling OWNER TO modeling;

-- Initialize modeling_platform database
\c modeling_platform;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE SCHEMA IF NOT EXISTS public;

GRANT ALL PRIVILEGES ON DATABASE modeling_platform TO modeling;
GRANT ALL PRIVILEGES ON SCHEMA public TO modeling;
ALTER DATABASE modeling_platform OWNER TO modeling;

ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO modeling;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO modeling;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO modeling;

-- Log success
DO $$
BEGIN
    RAISE NOTICE '================================================';
    RAISE NOTICE 'PostgreSQL Initialization Complete!';
    RAISE NOTICE 'Databases: modeling, modeling_platform';
    RAISE NOTICE 'User: modeling (password: modeling_dev)';
    RAISE NOTICE '================================================';
END $$;
