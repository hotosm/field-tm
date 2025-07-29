-- ## Migration to:
-- * Add 'SENSITIVE' to project visibility enum

-- Start a transaction
BEGIN;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_type WHERE typname = 'projectvisibility'
    ) THEN
        IF NOT EXISTS (
            SELECT 1 FROM pg_enum 
            WHERE enumlabel = 'SENSITIVE' 
            AND enumtypid = 'projectvisibility'::regtype
        ) THEN
            ALTER TYPE public.projectvisibility ADD VALUE 'SENSITIVE';
        END IF;
    END IF;
END$$;

-- Commit the transaction
COMMIT;
