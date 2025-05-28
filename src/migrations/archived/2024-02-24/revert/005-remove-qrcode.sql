-- Start a transaction
BEGIN;

-- Add qr_code table
CREATE TABLE IF NOT EXISTS public.qr_code (
    id integer NOT NULL,
    filename character varying,
    image bytea
);
ALTER TABLE public.qr_code OWNER TO fmtm;
CREATE SEQUENCE public.qr_code_id_seq
AS integer
START WITH 1
INCREMENT BY 1
NO MINVALUE
NO MAXVALUE
CACHE 1;
ALTER TABLE public.qr_code_id_seq OWNER TO fmtm;
ALTER SEQUENCE public.qr_code_id_seq OWNED BY public.qr_code.id;
ALTER TABLE ONLY public.qr_code ALTER COLUMN id SET DEFAULT nextval(
    'public.qr_code_id_seq'::regclass
);
ALTER TABLE ONLY public.qr_code
ADD CONSTRAINT qr_code_pkey PRIMARY KEY (id);

-- Update field in tasks table
ALTER TABLE IF EXISTS public.tasks
DROP COLUMN IF EXISTS odk_token,
ADD COLUMN IF NOT EXISTS qr_code_id integer;
CREATE INDEX ix_tasks_qr_code_id ON public.tasks USING btree (qr_code_id);
ALTER TABLE ONLY public.tasks
ADD CONSTRAINT tasks_qr_code_id_fkey FOREIGN KEY (
    qr_code_id
) REFERENCES public.qr_code (id);

-- Commit the transaction
COMMIT;
