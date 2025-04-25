# Database Tips

## Access the database (psql)

### Option 1

Access the database container using psql on your local machine:

```bash
psql -d fmtm -U fmtm -h localhost
```

### Option 2

Access a PostgreSQL shell inside the fmtm-db container:

```bash
GIT_BRANCH=development

docker exec -it fmtm-${GIT_BRANCH}-fmtm-db-1 psql -U fmtm fmtm
```

And then connect to the database using this command:

```bash
\c fmtm
```

## A few helpful psql commands

- You can list all the databases using the command:

```bash
\l
```

- To list all the schemas of the currently connected database, use the command:

```bash
\dn
```

- To list all the functions in the current database, use the command:

```bash
\df
```

- To list all the views in the current database, use the command:

```bash
\dv
```

- To list all the users and roles, use the command:

```bash
\du
```

- To list all the tables in the current database, use the command:

```bash
\dt
```

- To describe a table, use the command:

```bash
\d table_name
```

Replace "table_name" with the name of the table you want to describe.

- To execute the last command again, use the command:

```bash
\g
```

- To view your command history, use the command:

```bash
\s
```

- To save your command history to a file, use the command:

```bash
\s filename
```

Replace "filename" with the name of the file you
want to save the command history to.

- To execute commands from a file, use the command:

```bash
\i filename
```

Replace "filename" with the name of the file
containing the commands you want to execute.

- To view a list of all psql commands, use the command:

```bash
\?
```

- To view help for a specific command, use the command:

```bash
\h command_name
```

Replace "command_name" with the name of the command you want help with.

- To exit psql, use the command:

```bash
\q
```

**Note:** If you make a change, don't forget to commit the change!

## Migrations

- Migrations are a way to manage changes to the database schema over time.
- They are handled automatically by a management script when Field-TM starts up.
- Individual SQL migration scripts are placed in the `src/backend/migrations` dir.
  - These should be idempotent, i.e. can run over and over without causing errors.
  - There should also be a commented out SQL script for how to revert the migration.
  - Scripts should be named sequentially,
    i.e. the first is 001-some-migration.sql,
    then they increment by one.
  - Example `000-remove-user-password.sql`:

```bash
-- ## Migration to remove password field from public.users (replaced with OSM OAuth)


-- ## Apply Migration
-- Start a transaction
BEGIN;
-- Drop the 'password' column if it exists
ALTER TABLE IF EXISTS public.users
DROP COLUMN IF EXISTS password;
-- Commit the transaction
COMMIT;


-- ## Revert Migration (comment above, uncomment below)
-- -- Start a transaction
-- BEGIN;
-- -- Add the 'password' column back if it doesn't exist
-- ALTER TABLE public.users
-- ADD COLUMN IF NOT EXISTS password character varying;
-- -- Commit the transaction
-- COMMIT;
```

- When the docker compose stack starts,
  an additional container starts up and runs a bash script once.
- The script generates a _table_ called `migrations`,
  which simply tracks the script name and execution date.
- The `migrations` _directory_ is scanned for new files,
  and if there is no record in the database of being applied,
  the migration is applied.

### Running Migrations Manually

If for any reason you need to run migrations manually,
there are a few options:

#### Restart the migrations container

```bash
docker compose restart migrations
```

#### Run the migration script in docker

This runs inside the backend container:

```bash
docker compose exec api bash /migrate-entrypoint.sh`
```

#### Run the migration script directly

Make sure you have the 4 env vars for the database
connection set on your machine,
then run the migration script directly:

```bash
bash src/backend/migrate-entrypoint.sh
```
