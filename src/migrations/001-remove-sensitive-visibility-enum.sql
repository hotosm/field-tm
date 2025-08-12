-- ## Migration to:
-- * Remove 'SENSITIVE' and 'INVITE_ONLY' from projectvisibility enum

BEGIN;

-- Step 1: Normalize data
UPDATE projects
SET visibility = 'PRIVATE'
WHERE visibility::text IN ('SENSITIVE', 'INVITE_ONLY');

-- Step 2: Clean up enum if needed
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_type WHERE typname = 'projectvisibility'
    ) THEN
        IF EXISTS (
            SELECT 1 FROM pg_enum
            WHERE enumtypid = 'projectvisibility'::regtype
            AND enumlabel IN ('SENSITIVE', 'INVITE_ONLY')
        ) THEN
            -- Rename old type
            ALTER TYPE projectvisibility RENAME TO projectvisibility_old;

            -- Create clean enum type
            CREATE TYPE projectvisibility AS ENUM ('PUBLIC', 'PRIVATE');

            -- Convert column to new enum
            ALTER TABLE projects
            ALTER COLUMN visibility TYPE projectvisibility
            USING visibility::text::projectvisibility;

            -- Drop old enum
            DROP TYPE projectvisibility_old;
        ELSE        
        END IF;
    ELSE
    END IF;
END$$;

COMMIT;
