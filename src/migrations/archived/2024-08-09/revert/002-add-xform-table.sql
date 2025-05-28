-- Start a transaction
BEGIN;

DROP TABLE public.xforms;
DROP SEQUENCE public.xforms_id_seq;

ALTER TABLE public.tasks
ADD COLUMN IF NOT EXISTS odk_token VARCHAR;

ALTER TABLE public.projects
DROP COLUMN IF EXISTS odk_token;

-- Commit the transaction
COMMIT;
