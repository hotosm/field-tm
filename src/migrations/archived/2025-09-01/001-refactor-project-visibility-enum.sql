BEGIN;

-- Step 1: Normalize data
UPDATE projects
SET visibility = 'PRIVATE'
WHERE visibility::text IN ('SENSITIVE', 'INVITE_ONLY');

-- Step 2: Clean up enum
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
            -- Rename old enum type
            ALTER TYPE projectvisibility RENAME TO projectvisibility_old;

            -- Create new enum type
            CREATE TYPE projectvisibility AS ENUM ('PUBLIC', 'PRIVATE');

            -- Drop default to allow type change
            ALTER TABLE projects ALTER COLUMN visibility DROP DEFAULT;

            -- Convert column to new enum
            ALTER TABLE projects
            ALTER COLUMN visibility TYPE projectvisibility
            USING visibility::text::projectvisibility;

            -- (Optional) Restore default if needed
            -- ALTER TABLE projects ALTER COLUMN visibility SET DEFAULT 'PRIVATE';

            -- Drop old enum type
            DROP TYPE projectvisibility_old;
        END IF;
    END IF;
END$$;

COMMIT;
