-- * Remove last_login_at from users.
-- * Restore NOT NULL constraint on author_id in projects.

-- Start a transaction
BEGIN;

-- Remove last_login_at column from users
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'users'
          AND column_name = 'last_login_at'
    ) THEN
        ALTER TABLE users DROP COLUMN last_login_at;
    END IF;
END $$;

-- Restore NOT NULL constraint on author_id in projects
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'projects'
          AND column_name = 'author_id'
          AND is_nullable = 'YES'
    ) THEN
        ALTER TABLE projects ALTER COLUMN author_id SET NOT NULL;
    END IF;
END $$;

-- Commit the transaction
COMMIT;
