-- ## Migration to:
-- * Add user_invites table

-- Start a transaction
BEGIN;

CREATE TABLE IF NOT EXISTS public.user_invites (
    token UUID DEFAULT gen_random_uuid(),
    project_id integer NOT NULL,
    role public.projectrole NOT NULL DEFAULT 'MAPPER',
    osm_username VARCHAR,
    email VARCHAR,
    expires_at timestamp with time zone DEFAULT now() + interval '7 days',
    used_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now()
);
ALTER TABLE public.user_invites OWNER TO fmtm;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'user_invites_pkey' 
        AND table_name = 'user_invites'
    ) THEN
        ALTER TABLE ONLY public.user_invites
        ADD CONSTRAINT user_invites_pkey PRIMARY KEY (token);
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_user_invites_project
ON public.user_invites USING btree (
    project_id
);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'user_invites_project_id_fkey' 
          AND table_name = 'user_invites'
    ) THEN
        ALTER TABLE ONLY public.user_invites
        ADD CONSTRAINT user_invites_project_id_fkey
        FOREIGN KEY (project_id) REFERENCES public.projects (id);
    END IF;
END $$;

-- Commit the transaction
COMMIT;
