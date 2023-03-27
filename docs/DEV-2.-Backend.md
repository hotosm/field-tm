# Backend Deployment for Development

The recommended way to run FMTM is with Docker. You can also develop on your local machine outside of Docker, see below.

> NOTE: If you haven't yet downloaded the Repository and setup your environment variables, please check the [Getting Started](https://github.com/hotosm/fmtm/blob/main/docs/DEV-1.-Getting-Started.md) wiki page.

Now let's get started!

## 1. Start the API with Docker

The easiest way to get up and running is by using the FMTM Docker deployment. Docker creates a virtual environment, isolated from your computer's environment, installs all necessary dependencies, and creates a container for each the database, the api, and the frontend. These containers talk to each other via the URLs defined in the docker-compose file and your env file.

### 1A: Starting the Containers

1. You will need to [Install Docker](https://docs.docker.com/engine/install/) and ensure that it is running on your local machine.
2. From the command line: navigate to the top level directory of the FMTM project.
3. From the command line run: `docker-compose pull`.
   This will pull the latest container builds from **main** branch.
4. Once everything is pulled, from the command line run: `docker compose up -d api`
5. If everything goes well you should now be able to **navigate to the project in your browser:** `http://127.0.0.1:8000/docs`

> Note: If the link doesn't work, check the logs with `docker logs fmtm_api`.

### 1B: Setup ODK Central User

The FMTM uses ODK Central to store ODK data. By default, the docker setup includes a Central server.

1. Create a user with the email you provided in the **ODK_CENTRAL_USER** field of your `.env` file using the following command:    
  `docker compose exec central odk-cmd --email YOUREMAIL@ADDRESSHERE.com user-create`
2. When prompted to put a password, input the password you provided in the **ODK_CENTRAL_PASSWD** field of the `.env` file
3. Promote the user created to an admin using the following command:  
  `docker-compose exec central odk-cmd --email YOUREMAIL@ADDRESSHERE.com user-promote`

> Note: Alternatively, you may use an external Central server and user.

### 1C: Import Test Data

Some test data is available to get started quickly.

1. Navigate to the `import-test-data` endpoint in the API docs page:
  <http://127.0.0.1:8000/docs#/debug/import_test_data_debug_import_test_data_get>
2. Click `Try it out`, then `execute`.

## 2. Start the API locally (OUTDATED)

To run FMTM locally, you will need to start the database, the api, and the frontend separately, one by one. It is important to do this in the proper order.

### 2A: Starting the Database

#### Option 1: Run the Database (only) in Docker

Running the database in Docker means postgres/postgis does not need to be installed and ran on your local machine, and you can use the same database no matter your method of deployment.

1. You will need to [Install Docker](https://docs.docker.com/engine/install/) and ensure that it is running on your local machine.
2. From the command line, navigate into the top level directory of the FMTM project.
3. From the command line, start up database with `docker-compose -f docker-compose.local.yml up --build`

The `docker-compose.local.yml` file only includes the database container (`db`), so only the database runs on docker.

#### Option 2: Run the database locally

For advanced users, it is also possible to run a postgresql/postgis database locally, however you will need to set it up yourself, and may need to modify the `LOCAL_DEV_URL` environmental variable found in your `.env` file.

### 2B. Starting the API (not in docker)

After starting the database, from the command line:

1. Navigate to the top level directory of the FMTM project.
2. Create a virtual environment with: `python3 -m venv fmtm-env`. This ensures that your computer's Python environment is kept clean.
3. Start the FMTM virtual environment with: `source fmtm-env/bin/activate`
4. Install backend dependencies with: `pip install -r src/backend/requirements.txt`
5. Run the Fast API backend with: `uvicorn src.backend.main:api --reload`

The API should now be accessible at: <http://127.0.0.1:8000/docs>

## Backend Tips

### Implement authorization on an endpoints

To add authentication to an endpoint, import `login_required` from `auth` module, you can use it as a decorator or use fastapi `Depends(login_required)` on endpoints.

## Backend Debugging

1. Uncomment in docker-compose.yml:

```yaml
services:
  api:
    target: debug
    ports:
      - "5678:5678"
```

2. Re-build the docker image `docker compose build api`
3. Start the docker container `docker compose up -d api` (the api startup will be halted until you connect a debugger)
4. Set a debugger config in your IDE (e.g. VSCode) and start the debugger
5. The API server will start up & any set breakpoints will trigger

Example launch.json config for vscode:

```
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
          "localRoot": "${workspaceFolder}/src/backend",
          "remoteRoot": "/app/backend"
        }
      ],
      "justMyCode": false
    }
  ]
}
```

> Note: Either port 5678 needs to be bound to your localhost, or the `host` parameter can be set to the container IP address.
