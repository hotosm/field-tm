# Migrations

- Database setup in `init` dir.
- Migrations in this dir - applied in order by backend entrypoint.
- Migrations are archived after a release is made and pushed through to prod.

## Database Initialisation Scripts

- Under `init` we have some raw SQL scripts that setup the database.
- These are split logically into modules, then imported and executed
  in the `main.sql` file at first start.
- We also have `init/shared` as a few tables need to be duplicated
  in the mapper frontend PGLite implementation.
- This allows us to import and use these files as normal in the backend
  initialisation, but also selectively import just what we need into the
  mapper frontend.
