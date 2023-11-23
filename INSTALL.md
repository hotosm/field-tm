# Installation

## Software Requirements

It is recommended to run FMTM on a Linux-based machine.

> This includes MacOS, but some [tools must be
> substituted](#alternative-operating-systems).
>
> For Windows users, the easiest option is to use [Windows Subsystem for
> Linux](#alternative-operating-systems)

Before you can install and use this application, you will need to have
the following software installed and configured on your system:

> If running Debian/Ubuntu, the install script below does this for you.

[Git](https://git-scm.com/) to clone the FMTM repository.

[Docker](https://docs.docker.com/engine/install/)
to run FMTM inside containers.

[Docker Compose](https://docs.docker.com/compose/install)
for easy orchestration of the FMTM services.

> This is Docker Compose V2, the official Docker CLI plugin.
>
> i.e. `docker compose` commands, not `docker-compose` (the old tool).

## Easy Install

On a Linux-based machine with `bash` installed, run the script:

> Note: it is best to run this script as a user other than root.
>
> However, if you run as root, a user svcfmtm will be created for you.

```bash
# Option A) If you already cloned the repo
bash src/frontend/public/install.sh

# Option B) Download the script & run
curl -L https://get.fmtm.dev -o install.sh
bash install.sh
# Alternative URL: https://fmtm.hotosm.org/install.sh

# Then follow the prompts
```

## Manual Install

If more details are required, check out the
[dev docs](https://hotosm.github.io/fmtm/dev/Setup/)

### Table of Contents

1. [Clone the FMTM repository](#clone-the-fmtm-repository)
2. [Development: Setup Your Local Environment](#setup-your-local-environment)
3. [Start the API with Docker](#start-the-api-with-docker)
4. [Setup ODK Central User (Optional)](#setup-odk-central-user-optional)
5. [Import Test Data (Optional)](#import-test-data-optional)
6. [Check Authentication (Optional)](#check-authentication-optional)

### Clone the FMTM repository

Clone the repository to your local machine using the following command:

```bash
git clone https://github.com/hotosm/fmtm.git

# If you wish to deploy for production, change to the main branch
git checkout main
```

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

## Alternative Operating Systems

### Windows

Windows Subsystem for Linux (WSL) can be used to run Docker.

This will run a Linux machine inside Windows very efficiently.

To install follow the
[official instructions](https://learn.microsoft.com/en-us/windows/wsl/install).

Then continue with the FMTM [installation](#software-requirements).

### MacOS

[Colima](https://github.com/abiosoft/colima) is recommended
to run `docker` and `docker compose` commands.

Install colima, docker, docker compose using brew:

```sh
brew install colima
brew install docker docker-compose
```

Then configure the docker compose plugin to work on MacOS:

```sh
mkdir -p ~/.docker/cli-plugins

ln -sfn $(brew --prefix)/opt/docker-compose/bin/docker-compose ~/.docker/cli-plugins/docker-compose
```

Run Colima:

```sh
colima start
```

Then continue with the FMTM [installation](#software-requirements).

> Note: only tagged backend images are multi-architecture, supporting
> MacOS. The regular images for fast continuous deployment are not:
> `backend:development`, `backend:staging`, `backend:main`.

### A Note on Docker Desktop

While in theory FMTM should run using Docker-Desktop, it has not
been tested.

The authors opinion is that the official Linux Docker Daemon
should be installed in WSL or MacOS, instead of using Docker Desktop.

> Colima is a wrapper to run the Docker Daemon.

Although Docker Desktop may have a user friendly GUI, it simply
runs docker commands inside a Linux virtual machine underneath.

It is often easier and more flexible to do this yourself.
Plus it gives you access to all other other tools available
in a Linux operating system!
