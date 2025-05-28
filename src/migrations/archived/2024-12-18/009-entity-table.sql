-- ## Migration to:
-- * Add a new table that syncs the ODK Entity status to Field-TM.
-- * Add a primary key for entity_id field.
-- * Add two indexes on entity_id + project_id / task_id


-- Start a transaction
BEGIN;

CREATE TABLE IF NOT EXISTS public.odk_entities (
    entity_id UUID NOT NULL,
    status entitystate NOT NULL,
    project_id integer NOT NULL,
    task_id integer
);
ALTER TABLE public.odk_entities OWNER TO fmtm;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'odk_entities_pkey') THEN
        ALTER TABLE ONLY public.odk_entities
        ADD CONSTRAINT odk_entities_pkey PRIMARY KEY (entity_id);
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_entities_project_id
ON public.odk_entities USING btree (
    entity_id, project_id
);
CREATE INDEX IF NOT EXISTS idx_entities_task_id
ON public.odk_entities USING btree (
    entity_id, task_id
);

-- Commit the transaction
COMMIT;
