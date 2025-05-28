# Troubleshooting 🆘

## Running Field-TM standalone

- Although it's easiest to use Docker, sometimes it may no be feasible, or
  not preferred.
- We use a tool called `uv` to manage dependencies.
- Be careful when running Field-TM you are not accidentally pulling in your
  system packages.

### Tips

- Troubleshoot the packages `uv` sees with:
  `uv pip list`
- Check a package can be imported in the uv-based Python environment:

  ```bash
  uv run python
  import fastapi
  ```

If you receive errors such as:

```bash
pydantic.error_wrappers.ValidationError: 3 validation errors for Settings
OSM_URL
  field required (type=value_error.missing)
OSM_SCOPE
  field required (type=value_error.missing)
```

Then you need to set the env variables on your system.

Alternatively, run via `just`:

```bash
just start backend-no-docker
```

## Migrations

- Migrations are a way to manage changes to the database schema over time.
- They are handled automatically by a management script when Field-TM starts up.
- Individual SQL migration scripts are placed in the `src/migrations` dir.
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
