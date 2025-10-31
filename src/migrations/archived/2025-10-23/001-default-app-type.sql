-- Migration to add default for field_mapping_app

BEGIN;

-- Set default values based on use_odk_collect
DO $$
BEGIN
    UPDATE public.projects 
    SET field_mapping_app = 'ODK' 
    WHERE use_odk_collect = true 
    AND field_mapping_app IS NULL;
    
    UPDATE public.projects 
    SET field_mapping_app = 'FieldTM' 
    WHERE (use_odk_collect = false OR use_odk_collect IS NULL) 
    AND field_mapping_app IS NULL;
END $$;

-- Add default constraint for new rows
ALTER TABLE public.projects
ALTER COLUMN field_mapping_app
SET DEFAULT 'FieldTM';

COMMIT;
