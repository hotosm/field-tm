-- ## Migration to:
-- * Rename FMTM Public Beta org --> HOTOSM

-- Start a transaction
BEGIN;

-- Check if the organization with the new name 'HOTOSM' already exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM public.organisations WHERE slug = 'hotosm'
    ) THEN
        -- If 'HOTOSM' does not exist, update the organisation
        UPDATE public.organisations
        SET
            name = 'HOTOSM',
            slug = 'hotosm',
            description = 'Humanitarian OpenStreetMap Team'
        WHERE slug = 'fmtm-public-beta';
    END IF;
END $$;

-- Commit the transaction
COMMIT;
