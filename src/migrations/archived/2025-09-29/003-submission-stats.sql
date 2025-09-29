CREATE TABLE IF NOT EXISTS public.submission_daily_counts (
    id BIGSERIAL PRIMARY KEY,
    user_sub TEXT NOT NULL,
    project_id BIGINT NOT NULL,
    submission_date DATE NOT NULL,
    count INT NOT NULL DEFAULT 0,
    last_calculated TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_submission_daily_counts_user_date
ON public.submission_daily_counts (user_sub, submission_date);

CREATE INDEX IF NOT EXISTS idx_submission_daily_counts_user_project_date
ON public.submission_daily_counts (user_sub, project_id, submission_date);

CREATE TABLE IF NOT EXISTS public.submission_stats_cache (
    id BIGSERIAL PRIMARY KEY,
    user_sub TEXT NOT NULL,
    project_id BIGINT NOT NULL,
    total_valid_submissions INT NOT NULL DEFAULT 0,
    total_invalid_submissions INT NOT NULL DEFAULT 0,
    total_submissions INT NOT NULL DEFAULT 0,
    top_organisations JSONB NOT NULL DEFAULT '[]'::jsonb,
    top_locations JSONB NOT NULL DEFAULT '[]'::jsonb,
    last_calculated TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_submission_stats_cache_user
ON public.submission_stats_cache (user_sub);

CREATE INDEX IF NOT EXISTS idx_submission_stats_cache_user_project
ON public.submission_stats_cache (user_sub, project_id);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.table_constraints
        WHERE constraint_name = 'submission_daily_counts_user_sub_fkey'
          AND table_name = 'submission_daily_counts'
    ) THEN
        ALTER TABLE ONLY public.submission_daily_counts
        ADD CONSTRAINT submission_daily_counts_user_sub_fkey
        FOREIGN KEY (user_sub) REFERENCES public.users (sub) ON DELETE CASCADE;
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.table_constraints
        WHERE constraint_name = 'submission_daily_counts_project_fkey'
          AND table_name = 'submission_daily_counts'
    ) THEN
        ALTER TABLE ONLY public.submission_daily_counts
        ADD CONSTRAINT submission_daily_counts_project_fkey
        FOREIGN KEY (project_id) REFERENCES public.projects (id) ON DELETE CASCADE;
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.table_constraints
        WHERE constraint_name = 'submission_daily_counts_user_project_unique'
          AND table_name = 'submission_daily_counts'
    ) THEN
        ALTER TABLE ONLY public.submission_daily_counts
        ADD CONSTRAINT submission_daily_counts_user_project_unique
        UNIQUE (user_sub, project_id, submission_date);
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.table_constraints
        WHERE constraint_name = 'submission_stats_cache_user_sub_fkey'
          AND table_name = 'submission_stats_cache'
    ) THEN
        ALTER TABLE ONLY public.submission_stats_cache
        ADD CONSTRAINT submission_stats_cache_user_sub_fkey
        FOREIGN KEY (user_sub) REFERENCES public.users (sub) ON DELETE CASCADE;
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.table_constraints
        WHERE constraint_name = 'submission_stats_cache_project_fkey'
          AND table_name = 'submission_stats_cache'
    ) THEN
        ALTER TABLE ONLY public.submission_stats_cache
        ADD CONSTRAINT submission_stats_cache_project_fkey
        FOREIGN KEY (project_id) REFERENCES public.projects (id) ON DELETE CASCADE;
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.table_constraints
        WHERE constraint_name = 'submission_stats_cache_user_project_unique'
          AND table_name = 'submission_stats_cache'
    ) THEN
        ALTER TABLE ONLY public.submission_stats_cache
        ADD CONSTRAINT submission_stats_cache_user_project_unique
        UNIQUE (user_sub, project_id);
    END IF;
END $$;
