-- Add new values to the entitystate enum type
BEGIN;
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumlabel = 'NEW_GEOM' AND enumtypid = 'entitystate'::regtype) THEN
        ALTER TYPE entitystate ADD VALUE 'NEW_GEOM';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumlabel = 'VALIDATED' AND enumtypid = 'entitystate'::regtype) THEN
        ALTER TYPE entitystate ADD VALUE 'VALIDATED';
    END IF;
END$$;
COMMIT;
