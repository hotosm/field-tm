DO $$
BEGIN
    -- Step 1: Add 'sub' column to users if not exists
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'users' AND column_name = 'sub'
    ) THEN
        ALTER TABLE public.users ADD COLUMN sub VARCHAR;
        UPDATE public.users SET sub = CONCAT('osm|', id::text);
    END IF;

    -- Step 2: Drop foreign key constraints on referencing tables if they exist
    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'organisation_managers_user_id_fkey'
    ) THEN
        ALTER TABLE public.organisation_managers DROP CONSTRAINT organisation_managers_user_id_fkey;
    END IF;

    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'organisation_user_key'
    ) THEN
        ALTER TABLE public.organisation_managers DROP CONSTRAINT organisation_user_key;
    END IF;

    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'user_roles_user_id_fkey'
    ) THEN
        ALTER TABLE public.user_roles DROP CONSTRAINT user_roles_user_id_fkey;
    END IF;

    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_users'
        AND table_name = 'projects'
    ) THEN
        ALTER TABLE public.projects DROP CONSTRAINT fk_users;
    END IF;

    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_users'
        AND table_name = 'task_events'
    ) THEN
        ALTER TABLE public.task_events DROP CONSTRAINT fk_users;
    END IF;

    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_users'
        AND table_name = 'project_team_users'
    ) THEN
        ALTER TABLE public.project_team_users DROP CONSTRAINT fk_users;
    END IF;

    -- Step 3: For each referencing table, add 'user_sub' column and populate
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'organisation_managers' AND column_name = 'user_sub'
    ) THEN
        ALTER TABLE public.organisation_managers ADD COLUMN user_sub VARCHAR;
        UPDATE organisation_managers SET user_sub = CONCAT('osm|', user_id::text);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'task_events' AND column_name = 'user_sub'
    ) THEN
        ALTER TABLE public.task_events ADD COLUMN user_sub VARCHAR;
        UPDATE task_events SET user_sub = CONCAT('osm|', user_id::text);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'user_roles' AND column_name = 'user_sub'
    ) THEN
        ALTER TABLE public.user_roles ADD COLUMN user_sub VARCHAR;
        UPDATE user_roles SET user_sub = CONCAT('osm|', user_id::text);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'project_team_users' AND column_name = 'user_sub'
    ) THEN
        ALTER TABLE public.project_team_users ADD COLUMN user_sub VARCHAR;
        UPDATE project_team_users SET user_sub = CONCAT('osm|', user_id::text);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'projects' AND column_name = 'author_sub'
    ) THEN
        ALTER TABLE public.projects ADD COLUMN author_sub VARCHAR;
        UPDATE projects SET author_sub = CONCAT('osm|', author_id::text);
    END IF;

    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'organisations' AND column_name = 'created_by'
    ) THEN
        ALTER TABLE public.organisations ALTER COLUMN created_by TYPE VARCHAR;
        UPDATE organisations SET created_by = CONCAT('osm|', created_by::text);
    END IF;

    -- Step 4: Drop old ID fields (after verifying that all data has been migrated)
    PERFORM * FROM information_schema.columns WHERE table_name = 'organisation_managers' AND column_name = 'user_id';
    IF FOUND THEN
        ALTER TABLE public.organisation_managers DROP COLUMN user_id;
    END IF;

    PERFORM * FROM information_schema.columns WHERE table_name = 'task_events' AND column_name = 'user_id';
    IF FOUND THEN
        ALTER TABLE public.task_events DROP COLUMN user_id;
    END IF;

    PERFORM * FROM information_schema.columns WHERE table_name = 'user_roles' AND column_name = 'user_id';
    IF FOUND THEN
        ALTER TABLE public.user_roles DROP COLUMN user_id;
    END IF;

    PERFORM * FROM information_schema.columns WHERE table_name = 'project_team_users' AND column_name = 'user_id';
    IF FOUND THEN
        ALTER TABLE public.project_team_users DROP COLUMN user_id;
    END IF;

    PERFORM * FROM information_schema.columns WHERE table_name = 'projects' AND column_name = 'author_id';
    IF FOUND THEN
        ALTER TABLE public.projects DROP COLUMN author_id;
    END IF;

    PERFORM * FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'id';
    IF FOUND THEN
        ALTER TABLE public.users DROP COLUMN id;
    END IF;

    -- Step 5: Drop existing primary key constraint and create new primary key constraint on 'sub' column
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'users_pkey'
    ) THEN
        ALTER TABLE public.users ADD PRIMARY KEY (sub);
    END IF;

    ALTER TABLE ONLY public.users
    DROP CONSTRAINT IF EXISTS users_username_key;

    -- Step 6: Create new constraints
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'organisation_managers_user_sub_fkey'
        AND table_name = 'organisation_managers'
    ) THEN
        ALTER TABLE public.organisation_managers ADD CONSTRAINT organisation_managers_user_sub_fkey FOREIGN KEY (user_sub) REFERENCES users (sub);
    END IF;

    IF NOT EXISTS (
    SELECT 1 FROM information_schema.table_constraints
    WHERE constraint_name = 'organisation_user_key'
    AND table_name = 'organisation_managers'
    ) THEN
        ALTER TABLE public.organisation_managers ADD CONSTRAINT organisation_user_key UNIQUE (organisation_id, user_sub);
    END IF;

    IF NOT EXISTS (
    SELECT 1 FROM information_schema.table_constraints
    WHERE constraint_name = 'user_roles_pkey'
    AND table_name = 'user_roles'
    ) THEN
        ALTER TABLE public.user_roles ADD CONSTRAINT user_roles_pkey UNIQUE (user_sub, project_id);
    END IF;

    IF NOT EXISTS (
    SELECT 1 FROM information_schema.table_constraints
    WHERE constraint_name = 'project_team_users_pkey'
    AND table_name = 'project_team_users'
    ) THEN
        ALTER TABLE public.project_team_users ADD CONSTRAINT project_team_users_pkey UNIQUE (team_id, user_sub);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'task_events_user_sub_fkey'
        AND table_name = 'task_events'
    ) THEN
        ALTER TABLE public.task_events ADD CONSTRAINT task_events_user_sub_fkey FOREIGN KEY (user_sub) REFERENCES users (sub);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'user_roles_user_sub_fkey'
        AND table_name = 'user_roles'
    ) THEN
        ALTER TABLE public.user_roles ADD CONSTRAINT user_roles_user_sub_fkey FOREIGN KEY (user_sub) REFERENCES users (sub);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'project_team_users_user_sub_fkey'
        AND table_name = 'project_team_users'
    ) THEN
        ALTER TABLE public.project_team_users ADD CONSTRAINT project_team_users_user_sub_fkey FOREIGN KEY (user_sub) REFERENCES users (sub);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'projects_author_sub_fkey'
        AND table_name = 'projects'
    ) THEN
        ALTER TABLE public.projects ADD CONSTRAINT projects_author_sub_fkey FOREIGN KEY (author_sub) REFERENCES users (sub);
    END IF;

    -- Step 7: Recreate indexes
    DROP INDEX IF EXISTS idx_user_roles;
    DROP INDEX IF EXISTS idx_org_managers;
    DROP INDEX IF EXISTS idx_task_event_project_user;
    DROP INDEX IF EXISTS idx_task_event_user_id;

    CREATE INDEX IF NOT EXISTS idx_user_roles
    ON public.user_roles USING btree (
        project_id, user_sub
    );

    CREATE INDEX IF NOT EXISTS idx_org_managers
    ON public.organisation_managers USING btree (
        organisation_id, user_sub
    );

    CREATE INDEX IF NOT EXISTS idx_task_event_project_user
    ON public.task_events USING btree (
        user_sub, project_id
    );

    CREATE INDEX IF NOT EXISTS idx_task_event_user_sub
    ON public.task_events USING btree (
        task_id, user_sub
    );
END
$$;
