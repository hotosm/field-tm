# Deployment for Production

The following instructions are needed to set up Field-TM for production on
your own cloud server.

## Set up the Field-TM on a cloud server

### Set up a server and domain name

- Get a cloud server (tested with Ubuntu 22.04).
- Set up a domain name, and point the DNS to your cloud server.
- SSH into your server. Set up a user with sudo called
  svcfmtm. [this](https://www.digitalocean.com/community/tutorials/initial-server-setup-with-ubuntu-22-04)
  is a good guide for basic server setup including creation of a
  user.

### Run the install script

```bash
curl -L https://get.fmtm.dev -o install.sh
bash install.sh

# Then follow the prompts
```

#### Additional Environment Variables

Variables are set in `.env`.
Some can be updated manually, as required.

##### EXTRA_CORS_ORIGINS

> If extra cors origins are required for testing, the variable
> `EXTRA_CORS_ORIGINS` is a set of comma separated strings, e.g.:
> <http://fmtm.localhost:7050,http://some.other.domain>

##### API_PREFIX

> It is also possible to use the API_PREFIX variable if the api
> is served under, e.g. /api on the domain.
> However, this isn't the recommended approach, and testing is minimal.

##### CENTRAL_WEBHOOK_API_KEY

- This variable allows central-webhook to make requests to the backend API.
- We use this to update the feature/entity colours after mapping events occur.
- Create an API Key for user `svcfmtm`, which will add the key to the database.
- Set the key for the `CENTRAL_WEBHOOK_API_KEY` variable, and this should
  allow the webhook to work.

##### S3_ACCESS_KEY & S3_SECRET_KEY

> In most circumstances these variables should be provided
> to authenticate with your S3 provider.
> However, some providers (such as AWS), allow for
> `instance profiles` to be attached to your server,
> with required permissions preconfigured.
> By default connections made from the EC2 instance
> with attached `instance profile` will be automatically
> authenticated. S3_ACCESS_KEY and S3_SECRET_KEY should
> be set to blank strings in this case `=""`.

##### ODK\_ Variables

These can point to an externally hosted instance of ODK Central.

Or ODK Central can be started as part of the Field-TM docker compose
stack, and variables should be set accordingly.

#### Other Domains

If you run Field-TM with ODK and Minio (S3) included, then the
domains will default to:

```dotenv
${FMTM_DOMAIN} --> Frontend
api.${FMTM_DOMAIN} --> Backend
odk.${FMTM_DOMAIN} --> ODK Central
s3.${FMTM_DOMAIN} --> S3 / Minio
sync.${FMTM_DOMAIN} --> The DB Sync Service
mapper.${FMTM_DOMAIN} --> The Mapper UI
```

These defaults can be overridden with respective environment variables:

```dotenv
FMTM_API_DOMAIN
FMTM_ODK_DOMAIN
FMTM_S3_DOMAIN
FMTM_SYNC_DOMAIN
```

### Connecting to a remote database

- A database may be located on a headless Linux server in the cloud.
- To access the database via GUI tool such as PGAdmin,
  it is possible using port tunneling.

```bash
ssh username@server.domain -N -f -L {local_port}:localhost:{remote_port}

# Example
ssh root@fmtm.hotosm.org -N -f -L 5430:localhost:5433
```

This will map port 5432 on the remote machine to port 5430 on your local machine.

## Backup Process

- Backup Field-TM database:

  ```bash
  GIT_BRANCH=development
  backup_filename="fmtm-db-${GIT_BRANCH}-$(date +'%Y-%m-%d').sql.gz"
  echo $backup_filename

  docker exec -i -e PGPASSWORD=PASSWORD_HERE \
  fmtm-${GIT_BRANCH}-fmtm-db-1 \
  pg_dump --verbose --encoding utf8 --format c -U fmtm fmtm \
  | gzip -9 > "$backup_filename"
  ```

> Note: if you are dumping to import into a pre-existing
> database, you should also include the --clean flag.
>
> This will drop the existing tables prior to import,
> and should prevent conflicts.

- Backup ODK Central database:

  ```bash
  GIT_BRANCH=development
  backup_filename="fmtm-odk-db-${GIT_BRANCH}-$(date +'%Y-%m-%d').sql.gz"
  echo $backup_filename

  docker exec -i -e PGPASSWORD=PASSWORD_HERE \
  fmtm-${GIT_BRANCH}-central-db-1 \
  pg_dump --verbose --encoding utf8 --format c -U odk odk | \
  gzip -9 > "$backup_filename"
  ```

- Backup the S3 data:

```bash
GIT_BRANCH=development
backup_filename="fmtm-s3-${GIT_BRANCH}-$(date +'%Y-%m-%d').tar.gz"
echo $backup_filename

docker run --rm -i --entrypoint=tar \
-u 0:0 \
-v $PWD:/backups -v \
fmtm-s3-data-${GIT_BRANCH}:/mnt/data \
ghcr.io/hotosm/fmtm/backend:${GIT_BRANCH} \
-cvzf "/backups/$backup_filename" /mnt/data/
```

## Manual Database Restores

The restore should be as easy as:

```bash
# On a different machine (else change the container name)
GIT_BRANCH=development
backup_filename=fmtm-db-${GIT_BRANCH}-XXXX-XX-XX.sql.gz

cat "$backup_filename" | gunzip | \
docker exec -i -e PGPASSWORD=NEW_PASSWORD_HERE \
fmtm-${GIT_BRANCH}-fmtm-db-1 \
pg_restore --verbose -U fmtm -d fmtm

# For ODK
backup_filename=fmtm-odk-db-${GIT_BRANCH}-XXXX-XX-XX.sql.gz
cat "$backup_filename" | gunzip | \
docker exec -i -e PGPASSWORD=NEW_PASSWORD_HERE \
fmtm-${GIT_BRANCH}-central-db-1 \
pg_restore --verbose -U odk -d odk

# For S3 (with the backup file in current dir)
backup_filename=fmtm-s3-${GIT_BRANCH}-XXXX-XX-XX.tar.gz
docker run --rm -i --entrypoint=tar \
-u 0:0 --working-dir=/ \
-v $backup_filename:/$backup_filename -v \
ghcr.io/hotosm/fmtm/backend:${GIT_BRANCH} \
-xvzf "$backup_filename"
```

However, in some cases you may have existing data
in the database (i.e. if you started the docker
compose stack & the API ran the migrations!).

In this case you can import into a fresh db, before
attaching to the Field-TM containers:

```bash
export GIT_BRANCH=development

# Shut down the running database & delete the data
docker compose -f deploy/compose.$GIT_BRANCH.yaml down -v

# First, ensure you have a suitable .env with database vars
# Start the databases only
docker compose -f deploy/compose.$GIT_BRANCH.yaml up -d fmtm-db central-db

# (Optional) restore odk central from the backup
backup_filename=fmtm-central-db-${GIT_BRANCH}-XXXX-XX-XX-sql.gz

cat "$backup_filename" | gunzip | \
docker exec -i \
fmtm-${GIT_BRANCH}-central-db-1 \
pg_restore --verbose -U odk -d odk

# Restore fmtm from the backup
backup_filename=fmtm-db-${GIT_BRANCH}-XXXX-XX-XX-sql.gz

cat "$backup_filename" | gunzip | \
docker exec -i \
fmtm-${GIT_BRANCH}-fmtm-db-1 \
pg_restore --verbose -U fmtm -d fmtm

# Run the entire docker compose stack
docker compose -f deploy/compose.$GIT_BRANCH.yaml up -d
```

## Help! Field-TM Prod Is Broken 😨

### Debugging

- Log into the production server, fmtm.hotosm.org and view the container logs:

  ```bash
  docker logs fmtm-main-api-1
  docker logs fmtm-main-api-2
  docker logs fmtm-main-api-3
  docker logs fmtm-main-api-4
  ```

  > Note there are four replica containers running, and any one of them
  > could have handled the request. You should check them all.

  They often provide useful traceback information, including timestamps.

- View error reports on Sentry: <https://humanitarian-openstreetmap-tea.sentry.io>
  You can get very detailed tracebacks here, even with the SQL executed on
  the database amongst other things.

- Reproduce the error on your local machine!

### Making a hotfix

- Sometimes fixes just can't wait to go through the development -->
  staging --> production cycle. We need the fix now!

- In this case, a `hotfix` can be made directly to the `main` branch:
  - Create a branch `hotfix/something-i-fixed`, add your code and test
    it works locally.
  - Push your branch, then create a PR against the `main` branch in Github.
  - Merge in the PR and wait for the deployment.
  - Later the code can be pulled back into develop / staging.
