# Deployment for Production

The following instructions set up FMTM on your own cloud server.

## Configure a Linux Server

### Basic setup & domain name

- Get a cloud server (tested with Ubuntu 22.04).
- Set up a domain name, and point the DNS to your cloud server.
- SSH into your server.
  - Set up a user with sudo called fmtm.
  - [this](https://www.digitalocean.com/community/tutorials/initial-server-setup-with-ubuntu-22-04) is a good guide for basic server setup including creation of a user.

### Install Docker & the Compose Plugin

[Here](https://docs.docker.com/engine/install/ubuntu/) is a good tutorial. At the time of writing that consisted of:

      sudo apt update
      sudo apt install ca-certificates curl gnupg
      sudo install -m 0755 -d /etc/apt/keyrings
      curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
      sudo chmod a+r /etc/apt/keyrings/docker.gpg
      echo \
      "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | \
      sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
      sudo apt-get update
      sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

## Deploy FMTM Manually

### Grab the FMTM code

- Clone the Git repo for the fmtm with `git clone https://github.com/hotosm/fmtm.git`.
- Step into the resulting directory with `cd fmtm`.

### Set up the .env file

- Create the env file from the example with `cp .env.example .env`.
- Edit the file to contain additional keys (it should look like this):

```dotenv
# Deployment Environment
GIT_BRANCH=main

# ODK Central
ODK_CENTRAL_VERSION=v2023.2.1
ODK_CENTRAL_URL=https://central-proxy
ODK_CENTRAL_USER=`<CHANGEME>`
ODK_CENTRAL_PASSWD=`<CHANGEME>`

# FMTM
URL_SCHEME=https
API_URL=fmtm-api.hotosm.org
FRONTEND_MAIN_URL=fmtm.hotosm.org
FRONTEND_MAP_URL=map.fmtm.hotosm.org
# API_PREFIX=/api

# OSM
OSM_CLIENT_ID=`<CHANGEME>`
OSM_CLIENT_SECRET=`<CHANGEME>`
OSM_URL=https://www.openstreetmap.org
OSM_SCOPE=read_prefs
OSM_LOGIN_REDIRECT_URI=https://fmtm-api.hotosm.org/auth/callback/
OSM_SECRET_KEY=`<CHANGEME>`

FMTM_DB_HOST=fmtm-db
FMTM_DB_USER=fmtm
FMTM_DB_PASSWORD=`<CHANGEME>`
FMTM_DB_NAME=fmtm
```

> Note: Change the GIT_BRANCH to staging for a staging deploy.

> Note: It is also possible to use the API_PREFIX variable if the api is served under, e.g. /api on the domain.

Run the production (and staging) docker-compose config:
`docker compose -f docker-compose.deploy.yml up -d`

To deploy with an external ODKCentral (development):
`docker compose -f docker-compose.noodk.yml up -d`

> Note: The images should be built in Github Container Registry. If they don't exist, use the `--build` flag during run.

With any luck, this will launch the docker container where the project runs, and you can access the working website from the domain name!

## Deploy FMTM via Github Workflow

1. Create a Linux server, as above.
2. The workflows to deploy should already exist under `.gibhub/workflows`.
3. Create an Environment Secret `DOTENV`.

- Repo settings --> Secrets and variables --> Manage Environments.
- Create a new environment (prod, staging, dev).
- Create an Environment Secret in your environment called DOTENV.
- Add the contents of `.env` above to the secret (+ configure variables).

4. Push or PR to the repo, and the code will automatically deploy via the workflow.
