# Backend Deployment for Development

The recommended way to run Field-TM is with Docker.

You can also develop on your local machine outside of Docker,
see below.

> NOTE: If you haven't yet downloaded the Repository and
> setup your local environment, please check the docs
> [here](../INSTALL.md#setup-your-local-environment).

Now let's get started :thumbsup:

## 1. Start the API with Docker

The easiest way to get up and running is by using the
Field-TM Docker deployment. Docker creates a virtual environment,
isolated from your computer's environment, installs all necessary
dependencies, and creates a container for each the database, the api,
and the frontend. These containers talk to each other via the
URLs defined in the docker-compose file and your env file.

1. You will need to
   [Install Docker](https://docs.docker.com/engine/install/)
   and ensure that it is running on your local machine.
2. From the command line: navigate to the top level directory
   of the Field-TM project.
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

- Field-TM uses ODK Central to store ODK data.
- To facilitate faster development, the Docker setup includes a Central server.
- The credentials are provided via the `.env` file, and the default URL to
  access Central from within containers is: `https://odkcentral:8443`.

> Alternatively, you may provide credentials to an external Central server
> in the `.env`.

To run the local development setup without ODK Central (use external server):

```bash
dc --profile no-odk up -d

# Or via Just
just start without-central
```

## 2. Start the API without Docker

- To run Field-TM without Docker, you will need to start the database, then the API.
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

- Migrations can be written to `src/migrations`.
- Each file must be an SQL script that is:
  - Idempotent: can be run multiple times without consequence.
  - Atomic: Run within a BEGIN/COMMIT transaction.
- Migrations must also include an equivalent revert migration under:
  `src/migrations/revert`

#### Applying Migrations

- Should occur automatically as part of the docker
  compose stack (migration service).
- To run manually:

```bash
docker compose up -d migrations

# Or via Just
just migrate
```

### The Task Scheduler

- The backend runs a lightweight scheduling service via cron.
- The scripts called and intervals can be found in the `compose.yaml`
  scheduler service.
- As of 21th April 2025, we run:

```bash
# Task unlocking every 3hrs
* */3 * * * /opt/scheduler/unlock_tasks.py

# Check inactive users every Sunday 00:00
0 0 * * 0 /opt/scheduler/inactive_users.py

# Run project stats script every 10 mins
*/10 * * * * /opt/scheduler/project_stats.py
```

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

`osm-fieldwork` is an integral package for much of the functionality in Field-TM.

Creating a new release during development may not always be feasible.

- A development version of osm-fieldwork can be mounted into
  the Field-TM container via bind mount.
- Clone the osm-fieldwork repo to the same root directory as Field-TM.
- Uncomment the line in compose.yaml

```yaml
- ../osm-fieldwork/osm_fieldwork:/opt/python/lib/python3.12/site-packages/osm_fieldwork
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

- Run JOSM with Field-TM via Just:

```bash
just start josm
```

This adds JOSM to the docker compose stack for local development.

You can now call the JOSM API from Field-TM and changes will be
reflected in the GUI.

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

### Creating projects via the API

Field-TM supports API Keys, meaning in theory an external system could be used
to create projects and call API endpoints, using the key.

#### 1. Create an API key

- Log into Field-TM as you the user you wish to use.
- The user must have organization manager permission for creating new projects.
- Generate an API key by accessing the following endpoint in the same browser
  you logged in as:

  `/integrations/api-key`

- Save the API key somewhere safe! The key can access all your data in Field-TM!
- For any API call you make in the next section, ensure to set the `x-api-key`
  header. See the example in the next section!

#### 2. Create project metadata

The metadata for a project must be created first.

<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->

  !!! note
        This step assumes you already have an organization and connected ODK
        Central server configured. See [here](../manuals/project-managers.md)

<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->

- To create a project you will need the following:
  - Project name, description, instructions.
  - The ID of the organization you manage.
    - Visit `/auth/me` while logged in to retrieve this.
  - A GeoJSON of the area you wish to map.

- See further details of the exact endpoint requirements
  [here](https://hotosm.github.io/swagger/?url=https://docs.fmtm.dev/openapi/openapi.json#/projects/create_project_projects_post)

- Post the JSON data to the following endpoint: `/projects?org_id=xxx`

  ```python
  import os
  import requests

  FMTM_API_DOMAIN = os.getenv("FMTM_API_DOMAIN")
  FMTM_API_KEY = os.getenv("FMTM_API_KEY")

  response = requests.get(
    f"{FMTM_API_DOMAIN}/auth/me",
    headers={"x-api-key": FMTM_API_KEY},
  )
  org_id = response.json()["orgs_managed"][-1]

  project_data = {
    "name": "your new project",
    "short_description": "short details here",
    "description": "long details here",
    "per_task_instructions": "user mapping instructions here",
    "outline": {
        "coordinates": [
            [
                [85.317028828, 27.7052522097],
                [85.317028828, 27.7041424888],
                [85.318844411, 27.7041424888],
                [85.318844411, 27.7052522097],
                [85.317028828, 27.7052522097],
            ]
        ],
        "type": "Polygon",
    },
    "primary_geom_type": "POINT",
    "new_geom_type": "POINT",
    "task_split_type": "CHOOSE_AREA_AS_TASK",
    "hashtags": ["hashtag1", "hashtag2"],
    "visibility": "PRIVATE",
  }

  response = requests.post(
    f"{FMTM_API_DOMAIN}/projects?org_id={org_id}",
    headers={"x-api-key": FMTM_API_KEY},
    json=project_data,
  )

  project_id = response.json().id
  print(project_id)
  ```

- A successful POST will return a project_id, which you should save for
  later steps.

#### 3. Populate the tasks

- Task splitting can be done via multiple APIs.
  - By square: `/projects/split-by-square`.
  - By splitting algorithm: `/projects/split-by-sql`.
- For projects that require no task splitting, simply pass the AOI
  as the task area: `/projects/xxx/upload-task-boundaries`

  ```python
  import json

  task_geojson = json.dumps(
    {
      "coordinates": [
          [
              [85.317028828, 27.7052522097],
              [85.317028828, 27.7041424888],
              [85.318844411, 27.7041424888],
              [85.318844411, 27.7052522097],
              [85.317028828, 27.7052522097],
          ]
      ],
      "type": "Polygon",
    }
  ).encode("utf-8")

  task_geojson_file = {
      "task_geojson": (
          "file.geojson",
          BytesIO(task_geojson).read(),
      )
  }

  response = requests.post(
      f"{FMTM_API_DOMAIN}/projects/{project_id}/upload-task-boundaries",
      headers={"x-api-key": FMTM_API_KEY},
      files=task_geojson_file,
  )

  print(response.json())
  ```

#### 4. Submit the data you wish to map (optional)

```python
from io import BytesIO

with open("/path/to/your/data.geojson", "rb") as f:
    data_extracts = BytesIO(json.dumps(json.load(f)))

    data_extract_file = {
        "data_extract_file": (
            "file.geojson",
            data_extracts.read(),
        )
    }

response = requests.post(
    f"{FMTM_API_DOMAIN}/projects/{project_id}/upload-data-extract",
    headers={"x-api-key": FMTM_API_KEY},
    files=data_extract_file,
)

print(response.json())
```

#### 5. Generate the final project data

- For this step you need the XLSForm you wish to use for the survey.
  - Validate the form via this
    [link](https://api.fmtm.hotosm.org/docs#/projects/validate_form_projects_validate_form_post)
    first.

```python
from io import BytesIO
from pathlib import Path

xlsform_file = Path("/path/to/your/form.xls")
with open(xlsform_file, "rb") as xlsform_data:
    xlsform_obj = BytesIO(xlsform_data.read())

xform_file = {
    "xlsform": (
        "form.xls",
        xlsform_obj,
    )
}
response = requests.post(
    f"{FMTM_API_DOMAIN}/projects/{project_id}/generate-project-data",
    headers={"x-api-key": FMTM_API_KEY},
    files=xform_file,
)
```

You should have a project you can now access at:

`https://the.field.tm.domain/projects/{project_id}`
