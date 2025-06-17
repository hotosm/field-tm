-- ## Migration reset the _migrations table.

-- Start a transaction
BEGIN;
-- Create new enum type with all values

ALTER TYPE public.geomtype ADD VALUE IF NOT EXISTS 'MULTIPOLYLINE';
-- Commit the transaction
COMMIT;
