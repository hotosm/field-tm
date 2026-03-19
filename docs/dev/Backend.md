# Backend Deployment for Development

The recommended way to run Field-TM is with Docker via the `just` commands.

(if you wish to run without just, inspect the `tasks/` justfiles
for the underlying command used).

> NOTE: If you haven't yet downloaded the Repository and
> setup your local environment, please check the docs
> [here](../INSTALL.md#setup-your-local-environment).

Now let's get started :thumbsup:

## 1. Start Field-TM with Docker

The easiest way to get up and running:

```bash
# Generate the .env config file
just config generate-dotenv

# Start all services (auth disabled for local dev)
just start all
```

If everything goes well you should now be able to
**navigate to the project in your browser:**
`http://field.localhost:7050`

> Note: If that link doesn't work, check the logs with
> `docker compose logs backend`.
> Note: the database host `fieldtm-db` is automatically
> resolved by docker compose to the database container IP.

### Bundled ODK Central

- Field-TM uses ODK Central to store ODK data.
- To facilitate faster development, the Docker setup includes a Central server.
- The credentials are provided via the `.env` file, and the default URL to
  access Central from within containers is: `http://central:8383`.

> Alternatively, you may provide credentials to an external Central server
> in the `.env`.

To run the local development setup without ODK Central (use external server):

```bash
just start without-central
```

## 2. Start the backend without Docker

- To run Field-TM without Docker, you will need to start the database,
  then the backend.
- First start a Postgres database running on a port on your machine.
  - The database must have the Postgis extension installed.
- Then run:

```bash
just start backend-no-docker
```

Or manually:

1. Navigate to the backend directory under `src/backend`.
2. Install `uv` [via the official docs](https://docs.astral.sh/uv/getting-started/installation/)
3. Install backend dependencies with `uv`: `uv sync`
4. Run the Litestar backend with:
   `uv run uvicorn app.main:api --host 0.0.0.0 --port 8000`

The app should now be accessible at: <http://localhost:8000>

## Backend Tips

### Type Checking

- It is a good idea to have your code 'type checked' to avoid potential
  future bugs.
- To do this, install `pyright` (VSCode has an extension).

### Interactive Debugging

- The local version of the backend API that runs in `compose.yaml` includes the
  `debugpy` package and a port bind to `5678`.
- This means you should be able to simply click the 'debugger' toolbar in VSCode,
  then 'Remote - Server Debug'.
- When you add breakpoints to the code, the server should pause here to allow
  you to step through and debug code.
- The configuration for this is in `.vscode/launch.json`.

### Running Tests

To run the backend tests locally, run:

```bash
just test backend
```

To assess coverage of tests, run:

```bash
just test backend-coverage
```

To assess performance of endpoints:

- We can use the pyinstrument profiler.
- While in debug mode (DEBUG=True), access any endpoint.
- Add the `?profile=true` arg to the URL to view the execution time.

### Debugging osm-fieldwork

- `osm-fieldwork` is an integral package for much of the functionality in Field-TM.
- The package is stored in this monorepo under:
  `src/backend/packages/osm-fieldwork`
- This directory is mounted inside the backend by default
  during local development with `compose.yaml`.
- If you modify the code in the package, the container must be restarted
  to reflect this:
  `docker compose restart backend`

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
sudo mkdir /mnt/field-tm/local
sudo chown $(whoami):$(whoami) /mnt/field-tm/local
s3fs ftm-data /mnt/field-tm/local \
  -o passwd_file=/home/$(whoami)/s3-creds/field-tm-local \
  -o url=http://s3.field.localhost:7050 \
  -o use_path_request_style
```

Access the files like a directory under: `/mnt/field-tm/local`.

To mount permanently, add the following to `/etc/fstab`:

`ftm-data /mnt/field-tm/local fuse.s3fs _netdev,allow_other,\
use_path_request_style,passwd_file=/home/USERNAME/s3-creds/field-tm-local,\
url=http://s3.field.localhost:7050 0 0`

> Note: you should replace USERNAME with your linux username.

### Running JOSM in the dev stack

- Run JOSM with Field-TM via Just:

```bash
just start josm
```

This adds JOSM to the docker compose stack for local development.

You can now call the JOSM API from Field-TM and changes will be
reflected in the GUI.

### Debugging ODK Collect & QField when running on localhost

- ODK Collect and QField require externally accessible project servers
  to pull from.
- To achieve this for local development / debugging, a good solution is Cloudflare
  tunnelling (alternative to Ngrok).
- There is a helper script to do this automatically for you:

  ```bash
  just start tunnel
  ```

Once started, use the output URLs from the terminal during
project creation. The QRCodes should now work in ODK Collect
or QField (depending on project type).

> The credentials for the local ODK Central or QField instances
> are:
> Username: <admin@hotosm.org>
> Password: Password1234
