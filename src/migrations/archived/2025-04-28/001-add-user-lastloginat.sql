-- ## Migration add some extra fields.
-- * Add last_login_at to users.
-- * Remove NOT NULL constraint from author_id in projects.

-- Related issues:
-- https://github.com/hotosm/field-tm/issues/1999

-- Start a transaction

BEGIN;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'users'
          AND column_name = 'last_login_at'
    ) THEN
        ALTER TABLE users ADD COLUMN last_login_at TIMESTAMPTZ DEFAULT now();
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (
    SELECT 1
    FROM information_schema.columns
    WHERE table_name = 'projects'
        AND column_name = 'author_id'
        AND is_nullable = 'NO'
    ) THEN
        ALTER TABLE projects ALTER COLUMN author_id DROP NOT NULL;
    END IF;
END $$;

-- Commit the transaction
COMMIT;
