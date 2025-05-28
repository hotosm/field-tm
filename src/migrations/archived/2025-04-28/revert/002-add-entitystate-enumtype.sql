-- Revert migration: Remove 'NEW_GEOM' and 'VALIDATED' values
-- from the entitystate enum type
BEGIN;

DO $$
BEGIN
    -- Check if the unwanted enum values exist
    IF EXISTS (
        SELECT 1 
        FROM pg_enum 
        WHERE enumlabel IN ('NEW_GEOM', 'VALIDATED') 
        AND enumtypid = 'entitystate'::regtype
    ) THEN
        -- Step 1: Create a new enum type without the unwanted values
        CREATE TYPE public.entitystate_new AS ENUM (
            'READY',
            'OPENED_IN_ODK',
            'SURVEY_SUBMITTED',
            'MARKED_BAD'
        );
        ALTER TYPE public.entitystate_new OWNER TO fmtm;

        -- Step 2: Update rows with unwanted enum values
        -- Map 'NEW_GEOM' to 'READY' and 'VALIDATED' to 'SURVEY_SUBMITTED'
        UPDATE public.odk_entities
        SET status = 'READY'
        WHERE status = 'NEW_GEOM';

        UPDATE public.odk_entities
        SET status = 'SURVEY_SUBMITTED'
        WHERE status = 'VALIDATED';

        -- Step 3: Alter the column to use the new enum type
        ALTER TABLE public.odk_entities 
        ALTER COLUMN status TYPE public.entitystate_new 
        USING status::text::entitystate_new;

        -- Step 4: Drop the old enum type
        DROP TYPE public.entitystate;

        -- Step 5: Rename the new enum type to the original name
        ALTER TYPE public.entitystate_new RENAME TO entitystate;
    END IF;
END$$;

COMMIT;
