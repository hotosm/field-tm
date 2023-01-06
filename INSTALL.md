## Development

### Config:

    cp .env.example .env

Update the .env file with the desired settings.

### For the react frontend

From command line: 
    `cd src/frontend`
    `npm install`
    `npm run`

### To run locally with undockerized

#### api not in docker

In `docker-compose.yml` comment out `api` and `web`
From command line start up database with `docker compose up --build`

In `src/backend/database.py` switch from docker to local `SQLALCHEMY_DATABASE_URL`

From command line:

-   install dependencies with: `pip install -r src/backend/requirements.txt`
-   run fast api with: `uvicorn src.backend.main:api --host 0.0.0.0:5000 --reload`

#### flask frontend not in docker

-   start virtual envirnment with: `python3 -m venv fmtm-env`
    -   set it up with: `source fmtm-env/bin/activate`

-   install dependencies with: `pip install -r src/web/requirements.txt`

-   set env variables with: `export FLASK_APP=src/web/__init__.py`
    -   `export WEB_DOMAIN=${WEB_DOMAIN}`
    -   `eport API_URL=http&#x3A;//localhost:8000`
    -   `FLASK_DEBUG=1` (auto reloading on change)

-   run fast api with: `python3 src/web/manage_nf.py run`

### Start Docker Services:

    docker compose up --build

#### To put it in the background:

    docker compose up --build -d

### Debugging when using docker

Open tty to container

    docker attach fmtm-web-1

Add debug line in code

    import ipdb;ipdb.set_trace()

When this line is reached in the code then the attached tty window will 
become interactive with ipdb.

A few of those commands:
    [Command CheatSheet](https://wangchuan.github.io/coding/2017/07/12/ipdb-cheat-sheet.html)
    h(elp)
    w(here)
    d(own)
    u(p)
    b(reak): \[ ([filename:]lineno | function) [, condition] ]
    tbreak: \[ ([filename:]lineno | function) [, condition] ]
    cl(ear): \[bpnumber [bpnumber ...] ]
    disable bpnumber: [bpnumber ...]
    enable bpnumber: [bpnumber ...]
    ignore bpnumber count
    condition bpnumber condition
    s(tep)
    n(ext)
    unt(il)
    r(eturn)
    run [args ...]
    c(ont(inue))
    l(ist): \[first [,last]]
    a(rgs)
    p expression

Debugging commands

    help

To get out of debugging

    CTRL + D

## Database

### Database migrations

To migrate, make the changes in models.py
Start docker services `docker compose up`
Attach to web app container `docker compose exec web /bin/bash`
Run migration `FLASK_APP=src/web/__init__.py flask db migrate -m "[MIGRATION COMMENT]"`
Upgrade db `FLASK_APP=src/web/__init__.py flask db upgrade`

### Access database (psql):

Option #1:

    `docker exec -it fmtm-db-1 psql -U fmtm fmtm`

And then connect to the database

    `\c fmtm`

A few commands

    Switch connection to new database: `\c dbname`
    List databases: `\l`
    List all schemes of currently connected database: `\dn`
    List functions of current database: `\df`
    List views in current datbase: `\dv`
    List users and roles: `\du`

    List tables: `\dt`
    Describe a table: `\d table_name`

    Last command again: `\g`
    Command history: `\s`
    Save command history to file: `\s filename`
    Execute commands from file: `\i filename`
    List psql commands: `\?`
    Help: `\h`
    Exit: `\q`

If you make a change, don't forget to commit the change!

If you haven't implemented migrations yet and need to drop all tables, connect to fmtm and...

    drop table mapping_issue_categories cascade;
    drop table organisation_managers cascade;
    drop table organisations  cascade;
    drop table project_allowed_users cascade;
    drop table project_chat cascade;
    drop table project_info cascade;
    drop table project_teams cascade;
    drop table projects cascade;
    drop table task_history cascade;
    drop table task_invalidation_history cascade;
    drop table task_mapping_issues cascade;
    drop table tasks cascade;
    drop table teams cascade;
    drop table user_licenses cascade;
    drop table users cascade;
    drop table x_form cascade;

## Production

### Config:

    cp .env.example .env

Update the .env file with the desired settings.

### Start services:

    docker compose -f docker-compose.prod.yml up -d --build

## Testing

    pip install -r src/web/requirements.txt
    python -m pytest

## Troubleshooting

    # list all containers
    docker ps -a

    # turns everything off
    docker compose down

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

# TODO: set up ssl certificates.

It seems we're using Traefik as the reverse proxy web server, so my existing knowledge of how to set up ssl certs with LetsEncrypt is not applicable; probably something like [this](https://doc.traefik.io/traefik/https/acme/)
