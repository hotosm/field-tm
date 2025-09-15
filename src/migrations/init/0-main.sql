--
-- PostgreSQL database dump
--

-- Dumped from database version 14.9
-- Dumped by pg_dump version 15.3 (Debian 15.3-0+deb12u1)

-- Started on 2023-10-05 12:55:27 UTC


-- Setup

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET TIME ZONE 'UTC';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

ALTER SCHEMA public OWNER TO fmtm;

-- PostGIS

CREATE SCHEMA IF NOT EXISTS tiger;
ALTER SCHEMA tiger OWNER TO fmtm;

CREATE SCHEMA IF NOT EXISTS tiger_data;
ALTER SCHEMA tiger_data OWNER TO fmtm;

CREATE SCHEMA IF NOT EXISTS topology;
ALTER SCHEMA topology OWNER TO fmtm;

CREATE EXTENSION IF NOT EXISTS fuzzystrmatch WITH SCHEMA public;
CREATE EXTENSION IF NOT EXISTS postgis WITH SCHEMA public;
CREATE EXTENSION IF NOT EXISTS postgis_tiger_geocoder WITH SCHEMA tiger;
CREATE EXTENSION IF NOT EXISTS postgis_topology WITH SCHEMA topology;
-- Required for area-splitter PostGIS StraightSkeleton usage
CREATE EXTENSION IF NOT EXISTS postgis_sfcgal WITH SCHEMA public;


-- Enums
\i './1-enums.sql'

-- Extra
SET default_tablespace = '';
SET default_table_access_method = heap;

-- Tables
\i './2-tables.sql'
-- Constraints for primary keys
\i './3-constraints.sql'
-- Indexing
\i './4-indexes.sql'
-- Foreign keys
\i './5-foreign-keys.sql'

-- Triggers
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

CREATE OR REPLACE TRIGGER task_event_state_trigger
BEFORE INSERT ON public.task_events
FOR EACH ROW
EXECUTE FUNCTION public.set_task_state();

-- Finalise

REVOKE USAGE ON SCHEMA public FROM public;
GRANT ALL ON SCHEMA public TO public;
