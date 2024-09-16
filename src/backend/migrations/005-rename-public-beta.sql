-- ## Migration to:
-- * Rename FMTM Public Beta org --> HOTOSM

-- Start a transaction
BEGIN;

UPDATE public.organisations
SET
    name = 'HOTOSM',
    slug = 'hotosm',
    description = 'Humanitarian OpenStreetMap Team'
WHERE slug = 'fmtm-public-beta';

-- Commit the transaction
COMMIT;
