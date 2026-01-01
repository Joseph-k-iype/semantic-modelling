-- database/postgres/migrations/add_workspace_deleted_at.sql
-- Add soft delete support to workspaces table

-- Add deleted_at column if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'workspaces' 
        AND column_name = 'deleted_at'
    ) THEN
        ALTER TABLE workspaces 
        ADD COLUMN deleted_at TIMESTAMP WITH TIME ZONE;
        
        -- Add index for better query performance
        CREATE INDEX idx_workspaces_deleted_at ON workspaces(deleted_at);
        
        RAISE NOTICE 'Added deleted_at column to workspaces table';
    ELSE
        RAISE NOTICE 'deleted_at column already exists in workspaces table';
    END IF;
END $$;

-- Verify the column was added
SELECT 
    column_name, 
    data_type, 
    is_nullable 
FROM information_schema.columns 
WHERE table_name = 'workspaces' 
AND column_name = 'deleted_at';