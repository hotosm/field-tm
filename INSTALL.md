# Installation

## Software Requirements

It is recommended to run FMTM on a Linux-based machine.

> This includes MacOS, but some [tools must be substituted][1].
>
> For Windows users, the easiest option is to use [Windows Subsystem for Linux][2]

Before you can install and use this application, you will need to have
the following software installed and configured on your system:

> If running Debian/Ubuntu, the install script below does this for you.

[Git][3] to clone the FMTM repository.

[Docker][4]
to run FMTM inside containers.

[Docker Compose][5]
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
curl -L https://get.fmtm.dev -o install.sh
bash install.sh

# Then follow the prompts
```

## Manual Install

If more details are required, check out the
[dev docs][6]

### Table of Contents

- [Installation](#installation)
  - [Software Requirements](#software-requirements)
  - [Easy Install](#easy-install)
  - [Manual Install](#manual-install)
    - [Table of Contents](#table-of-contents)
    - [Clone the FMTM repository](#clone-the-fmtm-repository)
    - [Setup Your Local Environment](#setup-your-local-environment)
      - [1. Setup OSM OAUTH 2.0](#1-setup-osm-oauth-20)
      - [2. Create an `.env` File](#2-create-an-env-file)
    - [Start the API with Docker](#start-the-api-with-docker)
      - [Select the install type](#select-the-install-type)
      - [Pull the Images](#pull-the-images)
      - [Build the Frontend](#build-the-frontend)
      - [Start the Containers](#start-the-containers)
    - [Setup ODK Central User (Optional)](#setup-odk-central-user-optional)
    - [Set Up Monitoring (Optional)](#set-up-monitoring-optional)
    - [Check Authentication (Optional)](#check-authentication-optional)
  - [Alternative Operating Systems](#alternative-operating-systems)
    - [Windows](#windows)
    - [MacOS](#macos)
    - [A Note on Docker Desktop](#a-note-on-docker-desktop)

### Clone the FMTM repository

Clone the repository to your local machine using the following command:

```bash
git clone https://github.com/hotosm/fmtm.git

# If you wish to deploy for production, change to the main branch
git checkout main
```

### Setup Your Local Environment

These steps are essential to run and test your code!

#### 1. Setup OSM OAuth 2.0

The FMTM uses OAuth with OSM to authenticate users.

To properly configure your FMTM project, you will need to create keys for OSM.

1. [Login to OSM][28]
   (_If you do not have an account yet, click the signup
   button at the top navigation bar to create one_).

   Click the drop down arrow on the top right of the navigation bar
   and select My Settings.

2. Register your FMTM instance to OAuth 2 applications.

   Put your login redirect url as `http://127.0.0.1:7051/osmauth` if running locally,
   or for production replace with https://{YOUR_DOMAIN}/osmauth

   > Note: `127.0.0.1` is required for debugging instead of `localhost`
   > due to OSM restrictions.

   ![image][29]

3. Add required permissions:

   - 'Read user preferences' (`read_prefs`)
   - 'Send private messages to other users' (`send_messages`)

4. Now save your Client ID and Client Secret for the next step.

#### 2. Create an `.env` File

Environmental variables are used throughout this project.
To get started, create `.env` file in the top level dir,
a sample is located at `.env.example`.

This can be created interactively by running:

```bash
bash scripts/1-environment/gen-env.sh
```

> Note: If extra cors origins are required for testing, the variable
> `EXTRA_CORS_ORIGINS` is a set of comma separated strings, e.g.:
> <http://fmtm.localhost:7050,http://some.other.domain>
>
> Note: It is possible to generate the auth pub/priv key manually using:
> openssl genrsa -out fmtm-private.pem 4096
> openssl rsa -in fmtm-private.pem -pubout -out fmtm-private.pem

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
main - compose.main.yaml
staging - compose.staging.yaml
development - compose.development.yaml
local test - compose.yaml
```

Set your selection to a terminal variable to make the next step easier:

```bash
export GIT_BRANCH={your_selection}

# E.g.
export GIT_BRANCH=development
```

#### Pull the Images

```bash
docker compose -f "compose.${GIT_BRANCH}.yaml" pull
```

> This will pull the latest containers for the branch you selected.

#### Build the Frontend

Before we can run, you need to build your version of the frontend.

This is because the frontend contains variable specific to your deployment.

```bash
docker compose -f "compose.${GIT_BRANCH}.yaml" build ui
```

#### Start the Containers

```bash
docker compose -f "compose.${GIT_BRANCH}.yaml" up -d
```

You should see the containers start up in order.

Once complete, you should now be able to **navigate to the project in your browser:**

```text
https://{YOUR_DOMAIN}

# For the local test setup, this will be
http://fmtm.localhost:7050
```

> Note: If those link doesn't work, check the logs with `docker compose logs api`.
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

### Set Up Monitoring (Optional)

- There is an optional configuration for application monitoring via OpenTelemetry.
- To enable this set in your `.env` file:

  ```dotenv
  # For OpenObserve
  MONITORING="openobserve"
  # For Sentry
  MONITORING="sentry"
  ```

- Check the `.env.example` for additional required parameters.
- Everything should be configured for you to see endpoint calls in the
  selected web dashboard, providing full error tracebacks and stats.

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
[official instructions][30].

Then continue with the FMTM [installation][31].

### MacOS

[Colima][32] is recommended
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

Then continue with the FMTM [installation][33].

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

[1]: #alternative-operating-systems "tools must be substituted"
[2]: #alternative-operating-systems "Windows Subsystem for Linux"
[3]: https://git-scm.com/ "Git"
[4]: https://docs.docker.com/engine/install/ "Docker"
[5]: https://docs.docker.com/compose/install "Docker Compose"
[6]: https://docs.fmtm.dev/dev/Setup/ "dev docs"
[28]: https://www.openstreetmap.org/login "Login to OSM"
[29]: https://user-images.githubusercontent.com/36752999/216319298-1444a62f-ba6b-4439-bb4f-2075fdf03291.png "image"
[30]: https://learn.microsoft.com/en-us/windows/wsl/install "official instructions"
[31]: #software-requirements "installation"
[32]: https://github.com/abiosoft/colima "Colima"
[33]: #software-requirements "installation"
