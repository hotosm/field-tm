-- ## Migration to:
-- * Rename table mbtiles_path --> basemaps.
-- * Rename field basemaps.path --> basemaps.url.
-- * Update default background task status to 'PENDING'.
-- * Update background_tasks.id --> UUID type.
-- * Update basemaps.id --> UUID type.
-- * Also add a composite index to task_history on task_id and action_date

-- Start a transaction
BEGIN;

-- Mbtiles table

ALTER TABLE IF EXISTS public.mbtiles_path RENAME TO basemaps;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'basemaps' AND column_name = 'path') THEN
        ALTER TABLE public.basemaps RENAME COLUMN path TO url;
    END IF;
END $$;

ALTER TABLE public.basemaps ALTER COLUMN id DROP DEFAULT;
ALTER TABLE ONLY public.basemaps DROP CONSTRAINT IF EXISTS mbtiles_path_pkey;
DROP SEQUENCE IF EXISTS public.mbtiles_path_id_seq;

DO $$ 
BEGIN
    IF (
        SELECT data_type FROM information_schema.columns 
        WHERE table_name = 'basemaps' 
        AND column_name = 'id'
    ) != 'uuid' THEN
        ALTER TABLE public.basemaps 
        ALTER COLUMN id TYPE UUID USING gen_random_uuid();
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'basemaps_pkey'
          AND table_name = 'basemaps'
    ) THEN
        ALTER TABLE ONLY public.basemaps
        ADD CONSTRAINT basemaps_pkey PRIMARY KEY (id);
    END IF;
END $$;

-- Background tasks table

ALTER TABLE public.background_tasks ALTER status SET DEFAULT 'PENDING';
ALTER TABLE ONLY public.background_tasks DROP CONSTRAINT background_tasks_pkey;

DO $$ 
BEGIN
    IF (
        SELECT data_type FROM information_schema.columns 
        WHERE table_name = 'background_tasks' 
        AND column_name = 'id'
    ) != 'uuid' THEN
        ALTER TABLE public.background_tasks 
        ALTER COLUMN id TYPE UUID USING gen_random_uuid();
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'background_tasks_pkey'
          AND table_name = 'background_tasks'
    ) THEN
        ALTER TABLE ONLY public.background_tasks
        ADD CONSTRAINT background_tasks_pkey PRIMARY KEY (id);
    END IF;
END $$;

-- Create extra index on task_history

CREATE INDEX IF NOT EXISTS idx_task_history_date
ON public.task_history USING btree (
    task_id, action_date
);

-- Commit the transaction
COMMIT;
