-- ## Migration to:
-- * Set default values to respective fields in the table.

-- Start a transaction
BEGIN;

-- Update mbtiles_path table
ALTER TABLE public.mbtiles_path
ALTER COLUMN created_at SET DEFAULT now();

-- Update projects table
ALTER TABLE public.projects
ALTER COLUMN created SET DEFAULT now(),
ALTER COLUMN last_updated SET DEFAULT now(),
ALTER COLUMN status SET DEFAULT 'DRAFT',
ALTER COLUMN mapper_level SET DEFAULT 'INTERMEDIATE',
ALTER COLUMN priority SET DEFAULT 'MEDIUM',
ALTER COLUMN featured SET DEFAULT false;

-- Update task_history table
ALTER TABLE public.task_history
ALTER COLUMN action_date SET DEFAULT now();

-- Update tasks table
ALTER TABLE public.tasks
ALTER COLUMN task_status SET DEFAULT 'READY';

-- Update user_roles table
ALTER TABLE public.user_roles
ALTER COLUMN role SET DEFAULT 'MAPPER';

-- Update users table
ALTER TABLE public.users
ALTER COLUMN role SET DEFAULT 'MAPPER',
ALTER COLUMN is_email_verified SET DEFAULT false,
ALTER COLUMN is_expert SET DEFAULT false,
ALTER COLUMN mapping_level SET DEFAULT 'BEGINNER',
ALTER COLUMN tasks_mapped SET DEFAULT 0,
ALTER COLUMN tasks_validated SET DEFAULT 0,
ALTER COLUMN tasks_invalidated SET DEFAULT 0,
ALTER COLUMN date_registered SET DEFAULT now(),
ALTER COLUMN last_validation_date SET DEFAULT now();

-- Commit the transaction
COMMIT;
