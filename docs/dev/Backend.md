# Backend Deployment for Development

The recommended way to run FMTM is with Docker.

You can also develop on your local machine outside of Docker,
see below.

> NOTE: If you haven't yet downloaded the Repository and
> setup your local environment, please check the docs
> [here](../INSTALL.md#setup-your-local-environment).

Now let's get started :thumbsup:

## 1. Start the API with Docker

The easiest way to get up and running is by using the
FMTM Docker deployment. Docker creates a virtual environment,
isolated from your computer's environment, installs all necessary
dependencies, and creates a container for each the database, the api,
and the frontend. These containers talk to each other via the
URLs defined in the docker-compose file and your env file.

1. You will need to
   [Install Docker](https://docs.docker.com/engine/install/)
   and ensure that it is running on your local machine.
2. From the command line: navigate to the top level directory
   of the FMTM project.
3. From the command line run: `docker compose pull`.
   This will pull the latest container builds from **main** branch.
4. Make sure you have a `.env` file with all required variables, see
   [here](../INSTALL.md#2-create-an-env-file).
5. Once everything is pulled, from the command line run:
   `docker compose up -d api`
6. If everything goes well you should now be able to
   **navigate to the project in your browser:**
   `http://api.fmtm.localhost:7050/docs`

> Note: If that link doesn't work, check the logs with
> `docker compose logs api`.
> Note: the database host `fmtm-db` is automatically
> resolved by docker compose to the database container IP.

### Bundled ODK Central

- FMTM uses ODK Central to store ODK data.
- To facilitate faster development, the Docker setup includes a Central server.
- The credentials are provided via the `.env` file, and the default URL to
  access Central from within containers is: `https://proxy`.

> Alternatively, you may provide credentials to an external Central server
> in the `.env`.

To run the local development setup without ODK Central (use external server):

```bash
dc --profile no-odk up -d

# Or via Just
just start without-central
```

## 2. Start the API without Docker

- To run FMTM without Docker, you will need to start the database, then the API.
- First start a Postgres database running on a port on your machine.
  - The database must have the Postgis extension installed.
- After starting the database, from the command line:

1. Navigate to the backend directory under `src/backend`.
2. Install `uv` [via the official docs](https://docs.astral.sh/uv/getting-started/installation/)
3. Install backend dependencies with `uv`: `uv sync`
4. Run the Fast API backend with:
   `uv run uvicorn app.main:api --host 0.0.0.0 --port 8000`

The API should now be accessible at: <http://api.fmtm.localhost:7050/docs>

## Backend Tips

### Database Migration

#### Creating Migration Files

- Migrations can be written to `src/backend/migrations`.
- Each file must be an SQL script that is:
  - Idempotent: can be run multiple times without consequence.
  - Atomic: Run within a BEGIN/COMMIT transaction.
- Migrations must also include an equivalent revert migration under:
  `src/backend/migrations/revert`

#### Applying Migrations

- Should occur automatically as part of the docker
  compose stack (migration service).
- To run manually:

```bash
docker compose up -d migrations

# Or via Just
just migrate
```

### Type Checking

- It is a good idea to have your code 'type checked' to avoid potential
  future bugs.
- To do this, install `pyright` (VSCode has an extension).
- You may need to add the backend dependencies to `extraPaths`. In VSCode
  your settings.json would include:

```json
{
  "python.analysis.extraPaths": ["src/backend/__pypackages__/3.12/lib/"]
}
```

### Interactive Debugging

- The `docker-compose.yml` builds FMTM using the `debug` target in the Dockerfile.
- The debug image contains `debugpy` to assist debugging in the container.

To use it:

1. Re-build the docker image `docker compose build api`
2. Uncomment the debug port in docker-compose.yml:

   ```yml
   services:
     ...
     api:
       ...
       ports:
         - "7052:8000"
       #   - "5678:5678" # Debugger port
   ```

3. Start the docker container `docker compose up -d api`
4. Connect to the debugger on port **5678**.

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

### Running Tests

To run the backend tests locally, run:

```bash
docker compose run --rm api pytest

# Or via Just
just test backend
```

To assess coverage of tests, run:

```bash
docker compose run --rm --entrypoint='sh -c' api \
  'coverage run -m pytest && coverage report -m'

# Or via Just
just test coverage
```

To assess performance of endpoints:

- We can use the pyinstrument profiler.
- While in debug mode (DEBUG=True), access any endpoint.
- Add the `?profile=true` arg to the URL to view the execution time.

### Debugging osm-fieldwork

`osm-fieldwork` is an integral package for much of the functionality in FMTM.

Creating a new release during development may not always be feasible.

- A development version of osm-fieldwork can be mounted into
  the FMTM container via bind mount.
- Clone the osm-fieldwork repo to the same root directory as FMTM.
- Uncomment the line in docker-compose.yml

```yaml
- ../osm-fieldwork/osm_fieldwork:/home/appuser/.local/lib/python3.12/site-packages/osm_fieldwork
```

- Run the docker container with your local version of osm-fieldwork.
- Code changes to osm-fieldwork should be reflected immediately.
  If they are not, run:
  `docker compose restart api`.

> Note: this is useful for debugging features during active development.

### Accessing S3 Files use s3fs

The s3fs tool allows you to mount an S3 bucket on your filesystem,
to browse like any other directory.

Create a credentials file:

```bash
# Replace ACCESS_KEY_ID and SECRET_ACCESS_KEY
echo ACCESS_KEY_ID:SECRET_ACCESS_KEY > ${HOME}/.passwd-s3fs
chmod 600 ${HOME}/.passwd-s3fs
```

#### Mount local S3 using Just

```bash
just mount-s3
```

#### Mount S3 manually

Install s3fs:

```bash
sudo apt update
sudo apt install s3fs
```

Mount your bucket:

> If you wish for this to be permanent, see below.

```bash
sudo mkdir /mnt/fmtm/local
sudo chown $(whoami):$(whoami) /mnt/fmtm/local
s3fs fmtm-data /mnt/fmtm/local \
  -o passwd_file=/home/$(whoami)/s3-creds/fmtm-local \
  -o url=http://s3.fmtm.localhost:7050 \
  -o use_path_request_style
```

Access the files like a directory under: `/mnt/fmtm/local`.

To mount permanently, add the following to `/etc/fstab`:

`fmtm-data /mnt/fmtm/local fuse.s3fs _netdev,allow_other,\
use_path_request_style,passwd_file=/home/USERNAME/s3-creds/fmtm-local,\
url=http://s3.fmtm.localhost:7050 0 0`

> Note: you should replace USERNAME with your linux username.

### Running JOSM in the dev stack

- Run JOSM with FMTM via Just:

```bash
just start josm
```

This adds JOSM to the docker compose stack for local development.

You can now call the JOSM API from FMTM and changes will be reflected in the GUI.

### Debugging ODK forms when running on localhost

- ODK Collect requires an externally accessible instance of Central.
- To achieve this for local development / debugging, a good solution is Cloudflare
  tunnelling (alternative to Ngrok).
- There is a helper script to do this automatically for you:

  ```bash
  just start tunnel
  ```

Once started, use the output ODK Central URL from the terminal during
project creation. The QRCode should now work in ODK Collect.

> The credentials for the local ODK Central instance are:
> Username: <admin@hotosm.org>
> Password: Password1234
