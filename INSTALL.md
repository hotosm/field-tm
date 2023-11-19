# Installation

## Easy Way

Use the provided bash script:

```bash
# Option A) If you already cloned the repo
bash src/frontend/public/install.sh

# Option B) Download the script & run
curl -L https://get.fmtm.dev -o install.sh
bash install.sh
# Alternative URL: https://fmtm.hotosm.org/install.sh

# Then follow the prompts
```

> Note: it is best to run this script as a user other than root.
>
> However, if you run as root, a user svcfmtm will be created for you.

## Manual Way

If more details are required, check out the
[dev docs](https://hotosm.github.io/fmtm/dev/Setup/)

### Table of Contents

1. [Software Requirements](#software-requirements)

2. [Setting up FMTM](#setting-up-fmtm)

   - [Fork and Clone the FMTM repository](#fork-and-clone-the-fmtm-repository)
   - [Development: Setup Your Local Environment](#setup-your-local-environment)
   - [Start the API with Docker](#start-the-api-with-docker)
   - [Setup ODK Central User (Optional)](#setup-odk-central-user-optional)
   - [Import Test Data (Optional)](#import-test-data-optional)
   - [Check Authentication (Optional)](#check-authentication-optional)

## Software Requirements

Before you can install and use this application,
you will need to have the following software
installed and configured on your system:

- [Git](https://git-scm.com/)
- [Docker](https://docs.docker.com/)

To install Git, please follow the instructions on the
[official Git website](https://git-scm.com/downloads)

To install Docker, please follow the instructions on the
[official Docker website](https://docs.docker.com/engine/install/)

## Setting up FMTM

### Fork and Clone the FMTM repository

#### 1. Fork the repository

Forking creates a copy of the repository in your own GitHub account.
Go to the [Field Mapping Tasking Manager repository](https://github.com/hotosm/fmtm)
and click the "Fork" button in the top right corner of the page.

#### 2. Clone the forked repository

Clone the forked repository to your local machine using the following command:

```bash
git clone https://github.com/<your-username>/fmtm.git

# If you wish to deploy for production, change to the main branch
git checkout main
```

Make sure to replace `<your-username>` with your GitHub username.

### Setup Your Local Environment

These steps are essential to run and test your code!

#### 1. Setup OSM OAUTH 2.0

The FMTM uses OAUTH2 with OSM to authenticate users.

To properly configure your FMTM project, you will need to create keys for OSM.

1. [Login to OSM](https://www.openstreetmap.org/login)
   (_If you do not have an account yet, click the signup
   button at the top navigation bar to create one_).
   Click the drop down arrow on the top right of the navigation bar
   and select My Settings.

2. Register your FMTM instance to OAuth 2 applications.
   Put your login redirect url as `http://127.0.0.1:7051/osmauth/` if running locally,
   or for production replace with https://{YOUR_DOMAIN}/osmauth/

   > Note: `127.0.0.1` is required for debugging instead of `localhost`
   > due to OSM restrictions.

   ![image](https://user-images.githubusercontent.com/36752999/216319298-1444a62f-ba6b-4439-bb4f-2075fdf03291.png)

3. Only the _read user preferences permission_ is required as of now.

4. Now save your Client ID and Client Secret for the next step.

#### 2. Create an `.env` File

Environmental variables are used throughout this project.
To get started, create `.env` file in the top level dir,
a sample is located at `.env.example`.

This can be created interactively by running:

```bash
bash scripts/gen-env.sh
```

> Note: If extra cors origins are required for testing, the variable
> `EXTRA_CORS_ORIGINS` is a set of comma separated strings, e.g.:
> <http://fmtm.localhost:7050,http://some.other.domain>

### Start the API with Docker

This is the easiest way to get started with FMTM.

Docker runs each service inside **containers**, fully isolated from your
host operating system.

#### Prerequisite

You will need to [Install Docker](https://docs.docker.com/engine/install/)
and ensure that it is running on your local machine.

You will also need [Docker Compose](https://docs.docker.com/compose/install).
This is Docker Compose V2, the official Docker CLI plugin.
i.e. `docker compose` commands, not `docker-compose` (the old tool).

Then from the command line, navigate to the top level directory of the FMTM project.

#### Select the install type

Determine the what type of FMTM install you would like:

```text
main - the latest production
staging - the latest staging
development - the latest development (warning: may be unstable)
local test - used during development, or to start a test version
```

The corresponding docker-compose files are:

```text
main - docker-compose.main.yml
staging - docker-compose.staging.yml
development - docker-compose.development.yml
local test - docker-compose.yml
```

Set your selection to a terminal variable to make the next step easier:

```bash
export GIT_BRANCH={your_selection}

# E.g.
export GIT_BRANCH=development
```

#### Pull the Images

```bash
docker compose -f "docker-compose.${GIT_BRANCH}.yml" pull
```

> This will pull the latest containers for the branch you selected.

#### Build the Frontend

Before we can run, you need to build your version of the frontend.

This is because the frontend contains variable specific to your deployment.

```bash
docker compose -f "docker-compose.${GIT_BRANCH}.yml" build ui
```

#### Start the Containers

```bash
docker compose -f "docker-compose.${GIT_BRANCH}.yml" up -d
```

You should see the containers start up in order.

Once complete, you should now be able to **navigate to the project in your browser:**

```text
https://{YOUR_DOMAIN}

# For the local test setup, this will be
http://fmtm.localhost:7050
```

> Note: If those link doesn't work, check the logs with `docker logs fmtm-api`.
>
> Note: Use `docker ps` to view all container names.

### Setup ODK Central User (Optional)

The FMTM uses ODK Central to store ODK data.

- By default, the docker setup includes a Central server.
- The credentials should have been provided in your `.env`
  file to automatically create a user.
- To create a user manually:

```bash
docker compose exec central odk-cmd --email YOUREMAIL@ADDRESSHERE.com user-create
docker-compose exec central odk-cmd --email YOUREMAIL@ADDRESSHERE.com user-promote
```

> Note: Alternatively, you may use an external Central server and user.

### Import Test Data (Optional)

If running a local test version, test data is available to get started quickly.

- Navigate to the `import-test-data` endpoint in the API docs page:

<http://api.fmtm.localhost:7050/docs#/debug/import_test_data_debug_import_test_data_get>

- Click `Try it out`, then `execute`.

### Check Authentication (Optional)

Once you have deployed, you will need to check that you can properly authenticate.

1. Navigate to your frontend (e.g. `http://fmtm.localhost:7050`)

2. Click the 'Sign In' button and follow the popup prompts.

3. If successful, you should see your username in the header.

4. If you see an error instead, double check your credentials and
   redirect URL in the openstreetmap.org settings.

That's it, you have successfully set up FMTM!!
