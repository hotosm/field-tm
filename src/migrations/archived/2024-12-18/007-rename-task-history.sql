-- ## Migration to:
-- * Rename table task_history --> task_events.
-- * Rename columns https://github.com/hotosm/field-tm/issues/1610

-- Start a transaction
BEGIN;


-- Rename table
ALTER TABLE IF EXISTS public.task_history RENAME TO task_events;



-- Create new enums

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'taskevent') THEN
    CREATE TYPE public.taskevent AS ENUM (
        'MAP',
        'FINISH',
        'VALIDATE',
        'GOOD',
        'BAD',
        'CONFLATE',
        'SPLIT',
        'MERGE',
        'ASSIGN',
        'COMMENT'
    );
  END IF;
END $$;
ALTER TYPE public.taskevent OWNER TO fmtm;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'entitystate') THEN
    CREATE TYPE public.entitystate AS ENUM (
        'READY',
        'OPENED_IN_ODK',
        'SURVEY_SUBMITTED',
        'MARKED_BAD'
    );
  END IF;
END $$;
ALTER TYPE public.entitystate OWNER TO fmtm;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'mappingstate') THEN
    CREATE TYPE public.mappingstate AS ENUM (
        'UNLOCKED_TO_MAP',
        'LOCKED_FOR_MAPPING',
        'UNLOCKED_TO_VALIDATE',
        'LOCKED_FOR_VALIDATION',
        'UNLOCKED_DONE',
        'CONFLATED'
    );
  END IF;
END $$;
ALTER TYPE public.mappingstate OWNER TO fmtm;



-- Update task_events table

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'task_events' AND column_name = 'action') THEN
        -- Change from taskaction --> taskevent enum
        ALTER TABLE task_events
            ALTER COLUMN action TYPE public.taskevent
            USING CASE action
                WHEN 'RELEASED_FOR_MAPPING' THEN 'BAD'::public.taskevent
                WHEN 'LOCKED_FOR_MAPPING' THEN 'MAP'::public.taskevent
                WHEN 'MARKED_MAPPED' THEN 'FINISH'::public.taskevent
                WHEN 'LOCKED_FOR_VALIDATION' THEN 'VALIDATE'::public.taskevent
                WHEN 'VALIDATED' THEN 'GOOD'::public.taskevent
                WHEN 'MARKED_INVALID' THEN 'BAD'::public.taskevent
                WHEN 'MARKED_BAD' THEN 'BAD'::public.taskevent
                WHEN 'SPLIT_NEEDED' THEN 'SPLIT'::public.taskevent
                WHEN 'RECREATED' THEN 'BAD'::public.taskevent
                WHEN 'COMMENT' THEN 'COMMENT'::public.taskevent
                ELSE NULL
            END;

        -- Update task_event fields prior to trigger addition
        ALTER TABLE public.task_events ADD COLUMN state public.mappingstate;
        ALTER TABLE public.task_events RENAME COLUMN action TO event;
        ALTER TABLE public.task_events RENAME COLUMN action_text TO comment;
        ALTER TABLE public.task_events RENAME COLUMN action_date TO created_at;
    END IF;
END $$;



-- Drop old enums

DROP TYPE IF EXISTS public.taskaction;
-- Note this no longer used
DROP TYPE IF EXISTS public.taskstatus;



-- Create trigger function to set task state automatically

CREATE OR REPLACE FUNCTION set_task_state()
RETURNS TRIGGER AS $$
BEGIN
    CASE NEW.event
        WHEN 'MAP' THEN
            NEW.state := 'LOCKED_FOR_MAPPING';
        WHEN 'FINISH' THEN
            NEW.state := 'UNLOCKED_TO_VALIDATE';
        WHEN 'VALIDATE' THEN
            NEW.state := 'LOCKED_FOR_VALIDATION';
        WHEN 'GOOD' THEN
            NEW.state := 'UNLOCKED_DONE';
        WHEN 'BAD' THEN
            NEW.state := 'UNLOCKED_TO_MAP';
        WHEN 'SPLIT' THEN
            NEW.state := 'UNLOCKED_DONE';
        WHEN 'MERGE' THEN
            NEW.state := 'UNLOCKED_DONE';
        WHEN 'ASSIGN' THEN
            NEW.state := 'LOCKED_FOR_MAPPING';
        WHEN 'COMMENT' THEN
            NEW.state := OLD.state;
        ELSE
            RAISE EXCEPTION 'Unknown task event type: %', NEW.event;
    END CASE;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;



-- Apply trigger to task_events table
DO $$
BEGIN
    CREATE TRIGGER task_event_state_trigger
    BEFORE INSERT ON public.task_events
    FOR EACH ROW
    EXECUTE FUNCTION set_task_state();
EXCEPTION   
    WHEN duplicate_object THEN
        RAISE NOTICE 'Trigger task_event_state_trigger already exists. Ignoring...';
END$$;



-- Manually populate states for existing data
UPDATE task_events
SET state = CASE event
    WHEN 'MAP' THEN 'LOCKED_FOR_MAPPING'
    WHEN 'FINISH' THEN 'UNLOCKED_TO_VALIDATE'
    WHEN 'VALIDATE' THEN 'LOCKED_FOR_VALIDATION'
    WHEN 'GOOD' THEN 'UNLOCKED_DONE'
    WHEN 'BAD' THEN 'UNLOCKED_TO_MAP'
    WHEN 'SPLIT' THEN 'UNLOCKED_DONE'
    WHEN 'MERGE' THEN 'UNLOCKED_DONE'
    WHEN 'ASSIGN' THEN 'LOCKED_FOR_MAPPING'
    WHEN 'COMMENT' THEN state -- Preserve the existing state
END;




-- Add task_events foreign keys

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_projects') THEN
        ALTER TABLE ONLY public.task_events
            ADD CONSTRAINT fk_projects FOREIGN KEY (project_id)
            REFERENCES public.projects (id);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_project_task_id') THEN
        ALTER TABLE ONLY public.task_events
            ADD CONSTRAINT fk_project_task_id FOREIGN KEY (task_id, project_id)
            REFERENCES public.tasks (id, project_id);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_users') THEN
        ALTER TABLE ONLY public.task_events
            ADD CONSTRAINT fk_users FOREIGN KEY (user_id)
            REFERENCES public.users (id);
    END IF;
END $$;


-- Add default values for UUID fields
ALTER TABLE public.task_events
ALTER COLUMN event_id SET DEFAULT gen_random_uuid(),
ALTER COLUMN event_id SET NOT NULL,
ALTER COLUMN task_id SET NOT NULL,
ALTER COLUMN event SET NOT NULL,
ALTER COLUMN created_at SET DATA TYPE timestamp with time zone;

ALTER TABLE public.basemaps
ALTER COLUMN id SET DEFAULT gen_random_uuid(),
ALTER COLUMN id SET NOT NULL;

ALTER TABLE public.background_tasks
ALTER COLUMN id SET DEFAULT gen_random_uuid(),
ALTER COLUMN id SET NOT NULL;



-- Commit the transaction
COMMIT;
