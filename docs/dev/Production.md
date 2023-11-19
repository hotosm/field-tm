# Deployment for Production

The following instructions are needed to set up FMTM for production on
your own cloud server.

## Set up the FMTM on a cloud server

### Set up a server and domain name

- Get a cloud server (tested with Ubuntu 22.04).
- Set up a domain name, and point the DNS to your cloud server.
- SSH into your server. Set up a user with sudo called
  fmtm. [this](https://www.digitalocean.com/community/tutorials/initial-server-setup-with-ubuntu-22-04)
  is a good guide for basic server setup including creation of a
  user.

### Install some stuff it'll need

#### Docker

- Install
  Docker. [Here](https://www.digitalocean.com/community/tutorials/how-to-install-and-use-docker-on-ubuntu-22-04)
  is a good tutorial for that; do steps 1 and 2. At the time of
  writing that consisted of:

      sudo apt update
      sudo apt install apt-transport-https ca-certificates curl software-properties-common
      curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
      echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
      sudo apt update
      sudo apt install docker-ce
      sudo usermod -aG docker ${USER}
      su - ${USER}

- Now install Docker Compose (as per [this
  tutorial](https://www.digitalocean.com/community/tutorials/how-to-install-and-use-docker-compose-on-ubuntu-22-04)). At
  the time of writing (the latest version of Docker Compose may
  change, so the version number might be out of date, but the rest
  shouldn't change) this consisted of:

      mkdir -p ~/.docker/cli-plugins/
      curl -SL https://github.com/docker/compose/releases/download/v2.12.2/docker-compose-linux-x86_64 -o ~/.docker/cli-plugins/docker-compose
      sudo chmod +x ~/.docker/cli-plugins/docker-compose

### Grab the FMTM code

Clone the Git repo for the fmtm with `git clone https://github.com/hotosm/fmtm.git`. Step into the resulting directory
with `cd fmtm`.

### Set up the environment and utilities to launch

Create the env file interactively with:

```bash
bash scripts/gen-env.sh
```

OR

```bash
cp .env.example .env

# Then edit values manually
```

Main variables of note to update:

```dotenv
ODK_CENTRAL_USER=`<CHANGEME>`
ODK_CENTRAL_PASSWD=`<CHANGEME>`

CERT_EMAIL=`<EMAIL_ADDRESS_TO_GENERATE_CERT_FOR>`
OSM_CLIENT_ID=`<CHANGEME>`
OSM_CLIENT_SECRET=`<CHANGEME>`

S3_ACCESS_KEY=`<CHANGEME>`
S3_SECRET_KEY=`<CHANGEME>`
```

#### EXTRA_CORS_ORIGINS

> If extra cors origins are required for testing, the variable
> `EXTRA_CORS_ORIGINS` is a set of comma separated strings, e.g.:
> <http://fmtm.localhost:7050,http://some.other.domain>

#### API_PREFIX

> It is also possible to use the API_PREFIX variable if the api
> is served under, e.g. /api on the domain.
> However, this isn't the recommended approach, and testing is minimal.

#### S3_ACCESS_KEY & S3_SECRET_KEY

> In most circumstances these variables should be provided
> to authenticate with your S3 provider.
> However, some providers (such as AWS), allow for
> `instance profiles` to be attached to your server,
> with required permissions preconfigured.
> By default connections made from the EC2 instance
> with attached `instance profile` will be automatically
> authenticated. S3_ACCESS_KEY and S3_SECRET_KEY should
> be set to blank strings in this case `=""`.

#### ODK\_ Variables

These can point to an externally hosted instance of ODK Central.

Or ODK Central can be started as part of the FMTM docker compose
stack, and variables should be set accordingly.

#### Other Domains

If you run FMTM with ODK and Minio (S3) included, then the
domains will default to:

```
${FMTM_DOMAIN} --> Frontend
api.${FMTM_DOMAIN} --> Backend
odk.${FMTM_DOMAIN} --> ODK Central
s3.${FMTM_DOMAIN} --> S3 / Minio
```

These defaults can be overriden with respective environment variables:

```
FMTM_API_DOMAIN
FMTM_ODK_DOMAIN
FMTM_S3_DOMAIN
```

### Start the Compose Stack

Run the production docker-compose config:
`docker compose -f docker-compose.main.yml up -d`

> Note: The images should be built already on Github.

With any luck, this will launch the docker container where the project
runs, and you can access the working website from the domain name!

### Connecting to a remote database

- A database may be located on a headless Linux server in the cloud.
- To access the database via GUI tool such as PGAdmin, it is possible using port tunneling.

```bash
ssh username@server.domain -N -f -L {local_port}:localhost:{remote_port}

# Example
ssh root@fmtm.hotosm.org -N -f -L 5430:localhost:5433
```

This will map port 5432 on the remote machine to port 5430 on your local machine.

## Manual Database Backups

```bash
GIT_BRANCH=development
backup_filename="fmtm-db-backup-$(date +'%Y-%m-%d').sql.gz"
echo $backup_filename

docker exec -i -e PGPASSWORD=PASSWORD_HERE fmtm-db-${GIT_BRANCH} pg_dump --verbose --format c -U fmtm fmtm | gzip -9 > "$backup_filename"
```

## Manual Database Restores

```bash
# On a different machine (else change the container name)
GIT_BRANCH=development
backup_filename=fmtm-db-backup-XXXX-XX-XX-sql.gz

cat "$backup_filename" | gunzip | docker exec -i -e PGPASSWORD=NEW_PASSWORD_HERE fmtm-db-${GIT_BRANCH} pg_restore --verbose -U fmtm -d fmtm
```
