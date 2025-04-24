# Installation

## Software Requirements

It is recommended to run FieldTM on a Linux-based machine.

> This includes MacOS, but some [tools must be substituted][1].
>
> For Windows users, the easiest option is to use [Windows Subsystem for Linux][2]

Before you can install and use this application, you will need to have
the following software installed and configured on your system:

> If running Debian/Ubuntu, the install script below does this for you.

[Git][3] to clone the FieldTM repository.

[Docker][4]
to run FieldTM inside containers.

[Docker Compose][5]
for easy orchestration of the FieldTM services.

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
    - [Clone the FieldTM repository](#clone-the-fieldtm-repository)
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
    - [Configure Custom Branding](#configure-custom-branding)

### Clone the FieldTM repository

Clone the repository to your local machine using the following command:

```bash
git clone https://github.com/hotosm/fmtm.git

# If you wish to deploy for production, change to the main branch
git checkout main
```

### Setup Your Local Environment

These steps are essential to run and test your code!

#### 1. Setup OSM OAuth 2.0

The FieldTM uses OAuth with OSM to authenticate users.

To properly configure your FieldTM project, you will need to create keys for OSM.

1. [Login to OSM][7]
   (_If you do not have an account yet, click the signup
   button at the top navigation bar to create one_).

   Click the drop down arrow on the top right of the navigation bar
   and select My Settings.

2. Register your FieldTM instance to OAuth 2 applications.

   Put your login redirect url as `http://127.0.0.1:7051/osmauth` if running locally,
   or for production replace with https://{YOUR_DOMAIN}/osmauth

   > Note: `127.0.0.1` is required for debugging instead of `localhost`
   > due to OSM restrictions.

   ![image][8]

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

This is the easiest way to get started with FieldTM.

Docker runs each service inside **containers**, fully isolated from your
host operating system.

#### Select the install type

Determine the what type of FieldTM install you would like:

```text
main - the latest production
staging - the latest staging
development - the latest development (warning: may be unstable)
local test - used during development, or to start a test version
```

The corresponding docker-compose files are:

```text
main - deploy/compose.main.yaml
staging - deploy/compose.staging.yaml
development - deploy/compose.development.yaml
local test - compose.yaml
```

Set your selection to a terminal variable to make the next step easier:

```bash
export COMPOSE_FILE={your_selection}

# E.g.
export COMPOSE_FILE=deploy/compose.development.yaml
```

#### Pull the Images

```bash
docker compose -f "${COMPOSE_FILE}" pull
```

> This will pull the latest containers for the branch you selected.

#### Build the Frontend

Before we can run, you need to build your version of the frontend.

This is because the frontend contains variable specific to your deployment.

```bash
docker compose -f "${COMPOSE_FILE}" build ui
```

#### Start the Containers

```bash
docker compose -f "${COMPOSE_FILE}" up -d
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

The FieldTM uses ODK Central to store ODK data.

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

### Frontend Customization (Optional)

- It's possible to tailor the mapper portion of FieldTM to your needs (the main app
  that users will see).
- There is a `config.json` file that is used to dynamically modify the frontend
  deployment:

  ```json
  {
    "logoUrl": "/favicon.svg",
    "logoText": "Humanitarian OpenStreetMap Team",
    "cssFile": "https://cdn.jsdelivr.net/npm/@hotosm/ui@0.2.0-b6/dist/style.css",
    "enableWebforms": false,
    "loginProviders": {
      "osm": true,
      "google": true
    },
    "sidebarItemsOverride": []
  }
  ```

- This is read from the bundled Minio S3 bucket called `fmtm-data`:
  `https://s3.{YOUR_FIELDTM_DOMAIN}/fmtm-data/frontend/config.json`
- Under the `fmtm-data/frontend` path you can modify the `config.json`,
  and also upload things like CSS files and logos.

### Configure Custom Branding

- It's possible to replace the HOTOSM logo and change the colour scheme for your
  deployment.
- This file will be automatically picked up and used to style your application.
  By default, FieldTM will fallback to the bundled `config.json`.

  ```json
  {
      ...
      "logoUrl": "/favicon.svg",
      "logoText": "Humanitarian OpenStreetMap Team",
      "cssFile": "https://cdn.jsdelivr.net/npm/@hotosm/ui@0.2.0-b6/dist/style.css"
  }
  ```

### Configure Custom Sidebar Elements

- By default FieldTM has a few items in the sidebar, like a link to a support
  page, and other resources.
- These links can be overridden using the `sidebarItemsOverride` parameter in
  the `config.json`, which expects format:

  ```json
  {
      ...
      "sidebarItemsOverride": [
          {
              "name": "Your Website",
              "path": "https://yourwebsite.com"
          },
          {
              "name": "Support",
              "path": "https://docs.fmtm.dev/about/about/"
          }
      ]
  }
  ```

### Enabled / Disable Auth Providers

- We are continually adding new OAuth provider options.

  ```json
  {
    ...
      "loginProviders": {
          "osm": true,
          "google": true
      }
  }
  ```

That's it, you have successfully set up FieldTM!!

[1]: ./dev/Setup.md#alternative-operating-systems "MacOS container tools"
[2]: ./dev/Setup.md#alternative-operating-systems "Windows Subsystem for Linux"
[3]: https://git-scm.com/ "Git"
[4]: https://docs.docker.com/engine/install/ "Docker"
[5]: https://docs.docker.com/compose/install "Docker Compose"
[6]: https://docs.fmtm.dev/dev/Setup/ "dev docs"
[7]: https://www.openstreetmap.org/login "Login to OSM"
[8]: https://user-images.githubusercontent.com/36752999/216319298-1444a62f-ba6b-4439-bb4f-2075fdf03291.png "image"
