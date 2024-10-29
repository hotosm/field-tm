-- ## Migration to:
-- * Convert task_history.id from SERIAL to manual UUID field
-- * Remove DEFAULT from action_date (not supported by electric)

-- Start a transaction
BEGIN;

-- Drop default from action_date
ALTER TABLE IF EXISTS public.task_history ALTER COLUMN action_date DROP DEFAULT;

-- Add event_id field
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'task_history' AND column_name = 'id') THEN
        -- Add new event_id UUID field with values
        ALTER TABLE public.task_history ADD COLUMN event_id UUID;
        UPDATE public.task_history SET event_id = gen_random_uuid() WHERE event_id IS NULL;
        ALTER TABLE public.task_history ALTER COLUMN event_id SET NOT NULL;

        -- Drop the old integer column
        ALTER TABLE public.task_history DROP CONSTRAINT IF EXISTS task_history_pkey;
        ALTER TABLE public.task_history DROP COLUMN IF EXISTS id;
        DROP SEQUENCE IF EXISTS public.task_history_id_seq;
        
        -- Add primary key constraint on event_id column
        ALTER TABLE public.task_history ADD CONSTRAINT task_history_pkey PRIMARY KEY (event_id);
    END IF;
END $$;

-- Commit the transaction
COMMIT;
