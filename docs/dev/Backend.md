# Backend Deployment for Development

The recommended way to run FMTM is with Docker.

You can also develop on your local machine outside of Docker,
see below.

> NOTE: If you haven't yet downloaded the Repository and
> setup your environment variables, please check the
> [Getting Started](https://github.com/hotosm/fmtm/blob/main/docs/DEV-1-Getting-Started.md)
> wiki page.

Now let's get started :thumbsup:

## 1. Start the API with Docker

The easiest way to get up and running is by using the
FMTM Docker deployment. Docker creates a virtual environment,
isolated from your computer's environment, installs all necessary
dependencies, and creates a container for each the database, the api,
and the frontend. These containers talk to each other via the
URLs defined in the docker-compose file and your env file.

### 1A: Starting the Containers

1. You will need to
   [Install Docker](https://docs.docker.com/engine/install/)
   and ensure that it is running on your local machine.
2. From the command line: navigate to the top level directory
   of the FMTM project.
3. From the command line run: `docker-compose pull`.
   This will pull the latest container builds from **main** branch.
4. Make sure you have a `.env` file with all required variables, see
   [Getting Started](https://github.com/hotosm/fmtm/blob/main/docs/DEV-1.-Getting-Started.md).
5. Once everything is pulled, from the command line run:
   `docker compose up -d api`
6. If everything goes well you should now be able to
   **navigate to the project in your browser:**
   `http://api.fmtm.localhost:7050/docs`

> Note: If that link doesn't work, check the logs with
> `docker log fmtm-api`.
> Note: the database host `fmtm-db` is automatically
> resolved by docker compose to the database container IP.

- FMTM uses ODK Central to store ODK data.
- To facilitate faster development, the Docker setup includes a Central server.
- The credentials are provided via the `.env` file.

> Note: Alternatively, you may use an external Central server and user in the `.env`.

### 1B: Import Test Data

Some test data is available to get started quickly.

1. Navigate to the `import-test-data` endpoint in the API docs page:
   <http://api.fmtm.localhost:7050/docs#/debug/import_test_data_debug_import_test_data_get>
2. Click `Try it out`, then `execute`.

## 2. Start the API without Docker

To run FMTM without Docker, you will need to start the database, then the API.

### 2A: Starting the Database

#### Option 1: Run the Database (only) in Docker

Running the database in Docker means postgres does
not need to be installed on your local machine.

1. You will need to
   [Install Docker](https://docs.docker.com/engine/install/)
   and ensure that it is running on your local machine.
2. Start an instance of Postgres (with Postgis):

```bash
docker compose up -d fmtm-db
```

The database should be accessible at localhost:5438.

> Note: if port 5438 is already taken, then change the
> `-p ANY_PORT:5432` declaration.

#### Option 2: Run the database locally

For advanced users, it is also possible to run a
postgresql/postgis database locally, however you will
need to set it up yourself and make it accessible on a port.

### 2B. Starting the API

After starting the database, from the command line:

1. Navigate to the top level directory of the FMTM project.
2. Install PDM with: `pip install pdm`
3. Install backend dependencies with PDM: `pdm install`
4. Run the Fast API backend with:
   `pdm run uvicorn app.main:api --host 0.0.0.0 --port 8000`

The API should now be accessible at: <http://api.fmtm.localhost:7050/docs>

## 3. Hybrid Docker/Local

- It is not recommended to run FMTM in a container while
  using a local database on your machine.
- It is possible, but complicates the docker networking slightly.
- The FMTM container cannot see the local machine's
  `localhost`, so we need a workaround.
- **Option 1**: add `network_mode: "host"` under the `api:`
  service in the **docker-compose.yml** file.
- **Option 2**: use the direct container IP address for the
  database for **FMTM_DB_HOST**, found via `docker inspect fmtm_db`.

## Backend Tips

### Implement authorization on an endpoints

To add authentication to an endpoint, import `login_required`
from `auth` module, you can use it as a decorator or use
fastapi `Depends(login_required)` on endpoints.

### Database Migration

#### Creating Migration Files

- Exec into the API container: `docker compose exec api bash`.
- Run the command to generate migrations: `alembic revision`.
- The migration file should be generated under
  `src/backend/migrations/versions`.
- Commit the file to the repo.

#### Applying Migrations

- Should occur automatically as part of the docker
  compose stack (migration service).
- To run manually:

```bash
alembic upgrade head
```

## Backend Debugging

- The `docker-compose.yml` builds FMTM using the `debug` target in the Dockerfile.
- The debug image contains `debugpy` to assist debugging in the container.

To use it:

1. Re-build the docker image `docker compose build api`
2. Start the docker container `docker compose up -d api`
3. Connect to the debugger on port **5678**.

You can configure your IDE to do this with the build in debugger.

Example launch.json config for vscode:

```json
{
  "configurations": [
    {
      "name": "Remote - Server Debug",
      "type": "python",
      "request": "attach",
      "host": "localhost",
      "port": 5678,
      "pathMappings": [
        {
          "localRoot": "${workspaceFolder}/src/backend/app",
          "remoteRoot": "/opt/app"
        }
      ],
      "justMyCode": false
    }
  ]
}
```

> Note: either port 5678 needs to be bound to your localhost (default),
> or the `host` parameter can be set to the container IP address.

## Backend Testing

To run the backend tests locally, run:

```bash
docker compose run api pytest
```

## Using the local version of ODK Central

- During project creation a Central ODK URL must be provided.
- If you set up FMTM with docker and have ODK Central
  running in a container, you can use the URL:
  `https://proxy`
- The credentials should be present in your `.env` file.

## Debugging osm-fieldwork

`osm-fieldwork` is an integral package for much of the functionality in FMTM.

Creating a new release during development may not always be feasible.

- A development version of osm-fieldwork can be mounted into
  the FMTM container via bind mount.
- Clone the osm-fieldwork repo to the same root directory as FMTM.
- Uncomment the line in docker-compose.yml

```yaml
- ../osm-fieldwork/osm_fieldwork:/home/appuser/.local/lib/python3.10/site-packages/osm_fieldwork
```

- Run the docker container with your local version of osm-fieldwork.
- Code changes to osm-fieldwork should be reflected immediately.
  If they are not, run:
  `docker compose restart api`.

> Note: this is useful for debugging features during active development.

## Running JOSM in the dev stack

- Run JOSM with FMTM:

```bash
docker compose \
  -f docker-compose.yml \
  -f josm/docker-compose.yml \
  up -d
```

This adds JOSM to the docker compose stack for local development.
Access the JOSM Remote API: <http://localhost:8111>
Access the JOSM GUI in browser: <http://localhost:8112>

You can now call the JOSM API from FMTM and changes will be reflected in the GUI.

## Conclusion

Running the FMTM project is easy with Docker. You can also run the
project locally outside of Docker, but it requires more setup. The
frontend is built with React and Typescript, and the backend is built
with FastAPI. Use the tips provided to customize and extend the
functionality of the project.
