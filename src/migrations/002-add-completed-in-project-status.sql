-- ## Migration to:
-- * Add 'COMPLETED' to project status enum

-- Start a transaction
BEGIN;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_type WHERE typname = 'projectstatus'
    ) THEN
        IF NOT EXISTS (
            SELECT 1 FROM pg_enum 
            WHERE enumlabel = 'COMPLETED' 
            AND enumtypid = 'projectstatus'::regtype
        ) THEN
            ALTER TYPE public.projectstatus ADD VALUE 'COMPLETED';
        END IF;
    END IF;
END$$;

-- Commit the transaction
COMMIT;
