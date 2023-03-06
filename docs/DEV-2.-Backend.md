# Backend Deployment for Development

The recommended way to run FMTM is with Docker. You can also develop on your local machine outside of Docker, see below.

> NOTE: If you haven't yet downloaded the Repository and setup your environment variables, please check the [Development]() wiki page.

Now let's get started!

## 1. Start FMTM with Docker

The easiest way to get up and running is by using the FMTM Docker deployment. Docker creates a virtual environment, isolated from your computer's environment, installs all necessary dependencies, and creates a container for each the database, api, and frontend. These containers talk to each other via the URLs defined in the docker-compose file and your env file.

### 1A: Starting the Containers

1. You will need to [Install Docker](https://docs.docker.com/engine/install/) and insure that it is running on your local machine.
2. From the command line: navigate into the top level directory of the FMTM project.
3. From the command line run: `docker compose build`
4. Once everything is built, from the command line run: `docker compose up -d`

5. If everything goes well you should now be able to **navigate to the project in your browser:**
   - **Frontend:** <http://127.0.0.1:8080>
   - **API:** <http://127.0.0.1:8000/docs>

> Note: If those links don't work, check the logs with `docker log fmtm_api`.

### 1B: Setup ODK Central User

The FMTM uses ODK Central to store ODK data.

- By default the docker setup includes a Central server.
- Add an admin user, with the user (email) and password you included in `.env`:
  `docker compose exec central odk-cmd --email YOUREMAIL@ADDRESSHERE.com user-create`
  `docker-compose exec central odk-cmd --email YOUREMAIL@ADDRESSHERE.com user-promote`

> Note: Alternatively, you may use an external Central server and user.

## 2. Start FMTM locally

To run FMTM locally, you will need to start the database, the api, and the frontend separately, one by one. It is important to do this in the proper order.

### 2A: Starting the Database

#### Option 1: Run the Database (only) in Docker

Running the database in Docker means postgres/postgis does not need to be installed and ran on your local machine, and you can use the same database no matter your method of deployment.

1. You will need to [Install Docker](https://docs.docker.com/engine/install/) and insure that it is running on your local machine.
2. From the command line, navigate into the top level directory of the FMTM project.
3. From command line, start up database with `docker-compose -f docker-compose.local.yml up --build`

The `docker-compose.local.yml` file only includes the database container (`db`), so only the database runs on docker.

#### Option 2: Run the database locally

For advanced users, it is also possible to run a postgresql/postgis database locally, however you will need to set it up yourself, and may need to modify the `LOCAL_DEV_URL` environmental variable found in your `.env` file.

### 2B. Starting the API (not in docker)

After starting the database, from the command line:

1. Navigate into the top level directory of the FMTM project.
2. Create a virtual environment with: `python3 -m venv fmtm-env`. This ensures that your computer python environment is kept clean.
3. Start the FMTM virtual environment with: `source fmtm-env/bin/activate`
4. Install backend dependencies with: `pip install -r src/backend/requirements.txt`
5. Run the Fast API backend with: `uvicorn src.backend.main:api --reload`

The API should now be accessible at: <http://127.0.0.1:8000/docs>

### 2C. Starting the react frontend

To run the react frontend, from the command line:

1. Navigate into the react frontend directory: `cd src/frontend/main`
2. Install dependencies: `npm install`
3. Run the project: `npm run start:live`

The React frontend should now be accessible at: <http://127.0.0.1:8080>
