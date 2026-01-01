-- database/postgres/init/00-create-user-and-db.sql
-- This script must run FIRST to create the modeling_platform user and database
-- File naming with 00- ensures it runs before other initialization scripts

-- Create modeling_platform user if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT FROM pg_catalog.pg_user 
        WHERE usename = 'modeling_platform'
    ) THEN
        CREATE USER modeling_platform WITH 
            PASSWORD 'modeling_platform_password'
            CREATEDB
            LOGIN;
        
        RAISE NOTICE '✓ Created user: modeling_platform';
    ELSE
        RAISE NOTICE '✓ User modeling_platform already exists';
    END IF;
END
$$;

-- Grant necessary role attributes
ALTER USER modeling_platform WITH CREATEDB LOGIN;

-- Log user creation
DO $$
BEGIN
    RAISE NOTICE '============================================';
    RAISE NOTICE 'Database User Configuration';
    RAISE NOTICE '============================================';
    RAISE NOTICE 'Username: modeling_platform';
    RAISE NOTICE 'Password: modeling_platform_password';
    RAISE NOTICE 'Privileges: CREATEDB, LOGIN';
    RAISE NOTICE '============================================';
END
$$;