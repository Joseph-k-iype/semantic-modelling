#!/bin/bash
# database/postgres/init/00-create-user-and-db.sh
# This script MUST run FIRST to create the modeling user and modeling_platform database
# File naming with 00- ensures it runs before other initialization scripts

set -e

echo "============================================"
echo "Creating Database User and Database"
echo "============================================"

# Create modeling user if it doesn't exist
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    DO \$\$
    BEGIN
        IF NOT EXISTS (
            SELECT FROM pg_catalog.pg_user 
            WHERE usename = 'modeling'
        ) THEN
            CREATE USER modeling WITH 
                PASSWORD 'modeling_dev'
                CREATEDB
                LOGIN;
            
            RAISE NOTICE '✓ Created user: modeling';
        ELSE
            RAISE NOTICE '✓ User modeling already exists';
        END IF;
    END
    \$\$;

    -- Grant necessary role attributes
    ALTER USER modeling WITH CREATEDB LOGIN;
EOSQL

# Create modeling_platform database if it doesn't exist
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    SELECT 'CREATE DATABASE modeling_platform OWNER modeling'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'modeling_platform')\gexec
    
    GRANT ALL PRIVILEGES ON DATABASE modeling_platform TO modeling;
EOSQL

echo "✓ User 'modeling' created/verified"
echo "✓ Database 'modeling_platform' created/verified"
echo "✓ Permissions granted"
echo "============================================"