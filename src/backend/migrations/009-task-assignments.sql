-- Create sequence for team_name if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_sequences WHERE schemaname = 'public' AND sequencename = 'team_name_seq') THEN
        CREATE SEQUENCE public.team_name_seq
        AS integer
        START WITH 1
        INCREMENT BY 1
        NO MINVALUE
        NO MAXVALUE
        CACHE 1;
    END IF;
END $$;

-- Create project_teams table
CREATE TABLE IF NOT EXISTS public.project_teams (
    team_id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    team_name VARCHAR UNIQUE,
    project_id INTEGER NOT NULL
);

-- Alter project_teams table to set default value for team_name
ALTER TABLE public.project_teams
ALTER COLUMN team_name SET DEFAULT (
    'Team ' || nextval('public.team_name_seq'::regclass)
);

-- Set sequence ownership
ALTER SEQUENCE public.team_name_seq OWNED BY public.project_teams.team_name;

-- Add foreign key for project_id
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_projects' 
        AND table_name = 'project_teams'
    ) THEN
        ALTER TABLE public.project_teams
        ADD CONSTRAINT fk_projects FOREIGN KEY (project_id)
        REFERENCES public.projects (id) ON DELETE CASCADE;
    END IF;
END $$;


-- Create project_team_users table
CREATE TABLE IF NOT EXISTS public.project_team_users (
    team_id UUID,
    user_id INTEGER NOT NULL,
    PRIMARY KEY (team_id, user_id)
);

-- Add foreign key constraints for project_team_users
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'users'
        AND column_name = 'id'
    )
    AND NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_users'
        AND table_name = 'project_team_users'
    ) THEN
        ALTER TABLE public.project_team_users
        ADD CONSTRAINT fk_users FOREIGN KEY (user_id)
        REFERENCES public.users (id) ON DELETE CASCADE;
    END IF;
END $$;


-- Create index for project_team_users
CREATE INDEX IF NOT EXISTS idx_project_team_users_team_id
ON public.project_team_users USING btree (team_id);

-- Add team_id column to task_events if not exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'task_events' AND column_name = 'team_id'
    ) THEN
        ALTER TABLE public.task_events ADD COLUMN team_id UUID;
    END IF;
END $$;

-- Add foreign key constraint for team_id in task_events
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_team_id' 
        AND table_name = 'task_events'
    ) THEN
        ALTER TABLE public.task_events
        ADD CONSTRAINT fk_team_id FOREIGN KEY (team_id)
        REFERENCES public.project_teams (team_id);
    END IF;
END $$;
