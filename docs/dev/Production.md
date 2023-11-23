# Deployment for Production

The following instructions are needed to set up FMTM for production on
your own cloud server.

## Set up the FMTM on a cloud server

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
# Alternative URL: https://fmtm.hotosm.org/install.sh

# Then follow the prompts
```

#### Additional Environment Variables

Variables are set in `.env`.
Some can be updated manually, as required.

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

```dotenv
${FMTM_DOMAIN} --> Frontend
api.${FMTM_DOMAIN} --> Backend
odk.${FMTM_DOMAIN} --> ODK Central
s3.${FMTM_DOMAIN} --> S3 / Minio
```

These defaults can be overriden with respective environment variables:

```dotenv
FMTM_API_DOMAIN
FMTM_ODK_DOMAIN
FMTM_S3_DOMAIN
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

## Manual Database Backups

```bash
GIT_BRANCH=development
backup_filename="fmtm-db-${GIT_BRANCH}-$(date +'%Y-%m-%d').sql.gz"
echo $backup_filename

docker exec -i -e PGPASSWORD=PASSWORD_HERE \
fmtm-db-${GIT_BRANCH} \
pg_dump --verbose --format c -U fmtm fmtm \
| gzip -9 > "$backup_filename"

# For ODK
docker exec -i -e PGPASSWORD=PASSWORD_HERE \
fmtm-central-db-${GIT_BRANCH} \
pg_dump --verbose --format c -U odk odk | \
gzip -9 > "$backup_filename"
```

## Manual Database Restores

```bash
# On a different machine (else change the container name)
GIT_BRANCH=development
backup_filename=fmtm-db-${GIT_BRANCH}-XXXX-XX-XX-sql.gz

cat "$backup_filename" | gunzip | \
docker exec -i -e PGPASSWORD=NEW_PASSWORD_HERE \
fmtm-db-${GIT_BRANCH} \
pg_restore --verbose -U fmtm -d fmtm

# For ODK
cat "$backup_filename" | gunzip | \
docker exec -i -e PGPASSWORD=NEW_PASSWORD_HERE \
fmtm-central-db-${GIT_BRANCH} \
pg_restore --verbose -U odk -d odk
```
