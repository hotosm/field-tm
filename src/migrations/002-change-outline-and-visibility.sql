-- ## Migration to:
-- * Change visibility default to 'PUBLIC'
-- * Change outline data type to geometry(Geometry, 4326)

-- Start a transaction
BEGIN;

-- Removed https://github.com/hotosm/field-tm/issues/2791
-- DO $$
-- BEGIN
--     IF EXISTS (
--         SELECT 1
--         FROM information_schema.columns
--         WHERE table_schema = 'public'
--           AND table_name = 'projects'
--           AND column_name = 'outline'
--     ) THEN
--         ALTER TABLE public.projects
--         ALTER COLUMN outline TYPE geometry(Geometry, 4326)
--         USING outline::geometry(Geometry, 4326);
--     END IF;
-- END;
-- $$;


DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
            AND table_name = 'projects'
            AND column_name = 'visibility'
    ) THEN
        ALTER TABLE public.projects
        ALTER COLUMN visibility SET DEFAULT 'PUBLIC';
    END IF;
END $$;

-- Commit the transaction
COMMIT;
