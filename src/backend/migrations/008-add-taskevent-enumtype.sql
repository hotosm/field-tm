-- ## Migration to enable SFCGAL for usage of PostGIS StraightSkeleton function.

-- Start a transaction
BEGIN;

DO $$
BEGIN
    -- Check if 'RESET' already exists in the taskevent enum
    IF NOT EXISTS (
        SELECT 1
        FROM pg_enum
        WHERE enumlabel = 'RESET'
        AND enumtypid = 'taskevent'::regtype
    ) THEN
        -- Add 'RESET' to the taskevent enum
        ALTER TYPE public.taskevent ADD VALUE 'RESET';
    END IF;
END $$;


-- Recreate function to unlock task on reset
CREATE OR REPLACE FUNCTION public.set_task_state()
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
        WHEN 'RESET' THEN
            NEW.state := 'UNLOCKED_TO_MAP';
        ELSE
            RAISE EXCEPTION 'Unknown task event type: %', NEW.event;
    END CASE;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Recreate trigger to unlock task on reset
CREATE OR REPLACE TRIGGER task_event_state_trigger
BEFORE INSERT ON public.task_events
FOR EACH ROW
EXECUTE FUNCTION public.set_task_state();


-- Commit the transaction
COMMIT;
