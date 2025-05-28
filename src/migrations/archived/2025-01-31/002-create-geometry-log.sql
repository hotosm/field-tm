-- ## Migration to create a table to store new and bad geometries.

-- Start a transaction

BEGIN;

DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'geomstatus') THEN
        CREATE TYPE public.geomstatus AS ENUM ('BAD', 'NEW');
    END IF;
END $$;
ALTER TYPE public.geomstatus OWNER TO fmtm;

CREATE TABLE IF NOT EXISTS public.geometrylog (
    id SERIAL PRIMARY KEY,
    geom GEOMETRY NOT NULL,
    status geomstatus,
    project_id int,
    task_id int
);
ALTER TABLE public.geometrylog OWNER TO fmtm;

-- Indexes for efficient querying
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'geometrylog' AND column_name = 'geom') THEN
        CREATE INDEX IF NOT EXISTS idx_geometrylog ON geometrylog USING gist (geom);
    END IF;
END $$;

-- Commit the transaction
COMMIT;
