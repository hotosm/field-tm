# Deployment for Development

FMTM is Dockerized, but it is often faster to develop on your local machine outside of Docker. Therefore, instructions are given to run FMTM using docker, and in a mostly de-dockerized version. 

> NOTE: If you haven't yet downloaded the Repository and setup your environment variables, please check the [Development]() wiki page.

Now let's get started!

## 1. Fastest way to get up and running (Docker)

The easiest way to get up and running is by using the FMTM Docker deployment. Docker creates a virtual environment, isolated from your computer's environment, installs all necessary dependencies, and creates a container for each the database, api, and frontend. These containers talk to each other via the URLs defined in the docker-compose file and your env file. 

**To start FMTM via Docker:**

1. You will need to [Install Docker](https://docs.docker.com/engine/install/) and insure that it is running on your local machine.
2. From the command line: navigate into the top level directory of the FMTM project.
3. From the command line run: `docker compose up --build`

4. Check the command line for errors! If everything goes well you should now be able to **navigate to the project in your browser:**
    - **Demo frontend (_Deprecated_):** http://127.0.0.1:5000
    - **API:** http://127.0.0.1:8000/docs

> Note: If those links don't work, check the console log for the correct URLs. 

> Note: If you want to put Docker in the background, use the following command: `docker compose up --build -d`


## 2. Start FMTM locally (outside of Docker for quicker development)

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

The API should now be accessible at: http://127.0.0.1:8000/docs

### 2C. Starting the Demo Frontend (not in docker)

The demo frontend (found in `src/web`) is deprecated and will be replaced with `src/frontend` when feature parity is reached. However, as it is currently still useful, we are including it in this documentation

To run the demo frontend, from the command line:

1. Navigate into the top level directory of the FMTM project.
2. Create a virtual environment with: `python3 -m venv fmtm-env`. This ensures that your computer python environment is kept clean. 
3. Start the FMTM virtual environment with: `source fmtm-env/bin/activate`
4. Install frontend dependencies with: `pip install -r src/web/requirements.txt`
5. Set env variables with: 
    ```
    export FLASK_APP=src/web/__init__.py
    export WEB_DOMAIN=${WEB_DOMAIN}
    export API_URL=http://localhost:8000
    FLASK_DEBUG=1 #auto reloading on change
    ```

6. Run the demo frontend (a flask app) with: `python3 src/web/manage_nf.py run`

The Demo frontend should now be accessible at: http://127.0.0.1:5000

### 2D. Starting the react frontend (WIP - will replace Demo Frontend)

To run the react frontend, from the command line:

1. Navigate into the react frontend directory: `cd src/frontend`
2. Install dependencies: `npm install`
3. Run the project: `npm run`

The React frontend should now be accessible at: 

# Deployment for Production

The following instructions are needed set up FMTM for production on your own cloud server.

## Set up the FMTM on a cloud server

### Set up a server and domain name

-   Get a cloud server (tested with Ubuntu 22.04).
-   Set up a domain name, point the DNS to your cloud server.
-   SSH into your server. Set up a user with sudo called fmtm. [this](https://www.digitalocean.com/community/tutorials/initial-server-setup-with-ubuntu-22-04) is a good guide for basic server setup including creation of a user.

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

#### Python stuff

    sudo apt install python3-pip
    sudo apt install libpq-dev
    pip install -r src/web/requirements.txt

### Set up the environment and utilities to launch

Create the env file from the example with `cp .env.example .env`. Edit that file to contain the needful (it should look like this):

    # copy to .env and set variables
    FLASK_ENV=development
    WEB_DOMAIN=<domain name>
    METRICS_DOMAIN=fmtm-metrics.<domain name>

    # To generate login:
    # echo $(htpasswd -nb testuser password) | sed -e s/\\$/\\$\\$/g
    METRICS_LOGIN=

    DB_USER=fmtm
    DB_PASSWORD=fmtm
    DB_NAME=fmtm

Create a script to set some local variables and launch the FMTM. Call it `run-prod.sh`. It should contain:

    #!/bin/bash

    export WEB_DOMAIN=fieldmappingtm.org
    export METRICS_DOMAIN=fmtm-metrics.fieldmappingtm.org
    export METRICS_LOGIN=testuser:<hashed_stuff>

    docker compose -f docker-compose.prod.yml up -d

Make it executable with `sudo chmod +x run-prod.sh`.

Build it with `docker compose up --build -d`

Stop it with `docker compose stop`

Run it with `./run-prod.sh`.

With any luck, this will launch the docker container where the project runs, and you can access the working website from the domain name!

> TODO: set up ssl certificates.
> It seems we're using Traefik as the reverse proxy web server, so my existing knowledge of how to set up ssl certs with LetsEncrypt is not applicable; probably something like [this](https://doc.traefik.io/traefik/https/acme/)
