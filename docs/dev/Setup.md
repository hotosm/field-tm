# Contributor Setup

Use this guide if you want to develop or test Field-TM locally.

Field-TM is a LiteStar backend with HTMX templates. For local development, the
supported setup is:

- `src/backend` for application code
- Docker Compose for the full local stack
- `uv` for Python dependencies and direct backend runs

## Choose a local workflow

### Full stack with Docker

Use this when you want the normal development environment, including the local
database, proxy, ODK Central, and QField services.

```bash
git clone https://github.com/hotosm/field-tm.git
cd field-tm
just config generate-dotenv
just start dev
```

Open <http://field.localhost:7050>.

This local stack starts with `AUTH_PROVIDER=disabled`, so you can work on the
app without configuring login first.

Useful commands:

```bash
just stop all
docker compose logs backend
just start login
```

Use `just start login` if you need to test the bundled Hanko login flow instead
of running with auth disabled.

### Backend only, without Docker

Use this when you only need the Python app running directly on your machine.

Requirements:

- `uv` installed
- a running PostgreSQL database with PostGIS

Setup and run:

```bash
cd src/backend
uv sync
cd ../..
just start backend-no-docker
```

Open <http://localhost:8000>.

`just start backend-no-docker` compiles translations first, then starts the
backend with minimal local environment variables.

## Prerequisites

### Linux

Recommended for both development and production-style testing.

Install:

- `git`
- `just`
- Docker with the `docker compose` plugin
- `uv`

### macOS

macOS is supported for development, but container tooling must be provided by a
Linux VM layer such as Colima.

Example setup:

```bash
brew install colima docker docker-compose just uv
colima start
mkdir -p ~/.docker/cli-plugins
ln -sfn $(brew --prefix)/opt/docker-compose/bin/docker-compose ~/.docker/cli-plugins/docker-compose
```

Then follow the Docker workflow above.

### Windows

Use WSL2, then follow the Linux instructions inside WSL.

## Daily development commands

Install backend dependencies:

```bash
cd src/backend && uv sync
```

Run backend tests:

```bash
cd src/backend && uv run pytest -v tests
```

Run package tests:

```bash
cd src/backend && uv run pytest -v packages/osm-fieldwork/tests packages/area-splitter/tests
```

Run all backend tests:

```bash
cd src/backend && uv run pytest -v
```

Run lint and format hooks:

```bash
just lint
```

## Notes

- `just start dev` is the main local development entry point.
- `just start backend-no-docker` is only for backend-focused work and assumes
  you manage the database yourself.
- Local ODK credentials default to `admin@hotosm.org` / `Password1234`.
- Local QField admin credentials default to `sysadmin@hotosm.org` /
  `Password1234`.

## Troubleshooting

- If the app does not load, check `docker compose logs backend`.
- If containers start but requests fail, inspect `.env` and regenerate it with
  `just config generate-dotenv` if needed.
- For more details, see [Troubleshooting](./Troubleshooting.md).
- For production issues, see
  [Production Deployment](./Production.md#help-field-tm-is-broken).
