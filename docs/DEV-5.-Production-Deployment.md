# Deployment for Production

The following instructions are needed set up FMTM for production on your own cloud server.

## Set up the FMTM on a cloud server

### Set up a server and domain name

- Get a cloud server (tested with Ubuntu 22.04).
- Set up a domain name, point the DNS to your cloud server.
- SSH into your server. Set up a user with sudo called fmtm. [this](https://www.digitalocean.com/community/tutorials/initial-server-setup-with-ubuntu-22-04) is a good guide for basic server setup including creation of a user.

### Install some stuff it'll need

#### Docker

Install Docker. [Here](https://www.digitalocean.com/community/tutorials/how-to-install-and-use-docker-on-ubuntu-22-04) is a good tutorial for that; do step 1 and 2. At time of writing that consisted of:

    sudo apt update
    sudo apt install apt-transport-https ca-certificates curl software-properties-common
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt update
    sudo apt install docker-ce
    sudo usermod -aG docker ${USER}
    su - ${USER}

Now install Docker Compose (as per [this tutorial](https://www.digitalocean.com/community/tutorials/how-to-install-and-use-docker-compose-on-ubuntu-22-04)). At time of writing (the latest version of Docker Compose may change, so the version number might be out of date, but the rest shouldn't change) this consisted of:

    mkdir -p ~/.docker/cli-plugins/
    curl -SL https://github.com/docker/compose/releases/download/v2.12.2/docker-compose-linux-x86_64 -o ~/.docker/cli-plugins/docker-compose
    sudo chmod +x ~/.docker/cli-plugins/docker-compose

### Grab the FMTM code

Clone the Git repo for the fmtm with `git clone https://github.com/hotosm/fmtm.git`. Step into the resulting directory with `cd fmtm`.

### Set up the environment and utilities to launch

Create the env file from the example with `cp .env.example .env`. Edit that file to contain the needful (it should look like this):

    # ODK Central
    ODK_CENTRAL_URL=https://central-proxy
    ODK_CENTRAL_USER=`<CHANGEME>`
    ODK_CENTRAL_PASSWD=`<CHANGEME>`

    # FMTM
    API_URL=https://fmtm-api.hotosm.org
    FRONTEND_MAIN_URL=https://fmtm.hotosm.org
    FRONTEND_MAP_URL=https://map.fmtm.hotosm.org
    # API_PREFIX=/api

    # OSM
    OSM_CLIENT_ID=`<CHANGEME>`
    OSM_CLIENT_SECRET=`<CHANGEME>`
    OSM_URL=https://www.openstreetmap.org
    OSM_SCOPE=read_prefs
    OSM_LOGIN_REDIRECT_URI=`<YOUR_API_URL>`/auth/callback/
    OSM_SECRET_KEY=`<CHANGEME>`

    # Database (optional)
    CENTRAL_DB_HOST=central-db
    CENTRAL_DB_USER=odk
    CENTRAL_DB_PASSWORD=`<CHANGEME>`
    CENTRAL_DB_NAME=odk

    FMTM_DB_HOST=fmtm-db
    FMTM_DB_USER=fmtm
    FMTM_DB_PASSWORD=`<CHANGEME>`
    FMTM_DB_NAME=fmtm

> Note: It is also possible to use the API_PREFIX variable if the api is served under, e.g. /api on the domain.

Run the production docker-compose config:
`docker compose -f docker-compose.prod.yml up --build -d`

With any luck, this will launch the docker container where the project runs, and you can access the working website from the domain name!

> Note: don't forget to make an admin user for odkcentral [see Deployment page](https://github.com/hotosm/fmtm/wiki/DEV-2.-Deployment).
