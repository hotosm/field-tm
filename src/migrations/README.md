# Migrations

- Database setup in `init` dir.
- Migrations in this dir - applied in order by backend entrypoint.
- Migrations are archived after a release is made and pushed through to prod.

## Operator note for existing deployments

This repository does not maintain long-lived incremental Alembic-style
migration history. Releases track the current schema state under
`src/migrations/init/`.

For existing long-running deployments, validate schema compatibility before
upgrading. If your live database diverged from current `init` expectations,
perform a staged/manual migration plan first (and test on a backup) before
rolling the new backend.
