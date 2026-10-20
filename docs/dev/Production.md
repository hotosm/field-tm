# Production Deployment

**Helm is the supported production path.** The Docker Compose files in
`deploy/` still work, but are deprecated and community-supported
(see [below](#docker-compose-deprecated)).

## Helm

See [`chart/README.md`](../../chart/README.md) for all chart values.

### 1. Create secrets

```bash
kubectl create namespace field-tm
kubectl create secret generic api-ftm-vars --namespace field-tm \
  --from-literal=ENCRYPTION_KEY="$(openssl rand -base64 32)" \
  --from-literal=FTM_DB_HOST=your-db-host \
  --from-literal=FTM_DB_USER=fieldtm \
  --from-literal=FTM_DB_PASSWORD=xxxxxxx \
  --from-literal=FTM_DB_NAME=fieldtm \
  --from-literal=ODK_CENTRAL_URL=https://odk.example.com \
  --from-literal=ODK_CENTRAL_USER=xxxxxxx \
  --from-literal=ODK_CENTRAL_PASSWD=xxxxxxx
```

Any variable from the [configuration reference](#configuration-reference)
can go in this secret.

### 2. Install

```bash
helm upgrade --install field-tm oci://ghcr.io/hotosm/charts/field-tm \
  --namespace field-tm \
  --set existingSecret.name=api-ftm-vars \
  --set ingress.enabled=true \
  --set ingress.host=field.example.com \
  --set ingress.tls.enabled=true
```

Upgrade by re-running the same command with `--version <release>`.
Migrations run automatically in an init container.

### Auth

Field-TM's management app needs a Hanko login; the chart does not run one.

- **HOT deployments** use the default `auth.provider=hotosm` (login.hotosm.org).
- **Other organisations** run their own Hanko and set
  `auth.provider=bundled` with `auth.hankoApiUrl` (Hanko's public URL).
  Field-TM serves the login form at `/login`. Without Kubernetes, the
  compose stack below runs Hanko for you (`AUTH_PROVIDER=bundled`).
- `auth.provider=custom` is for your own Hanko plus your own login app
  (`auth.loginUrl`).

The task planner needs no login or backend: build `src/planner` and host the
static files anywhere (e.g. GitHub Pages).

### Monitoring

Create a secret with key `SENTRY_DSN` and set `sentry.existingSecret` to its
name. This sets `MONITORING=sentry`. Leave it unset to disable monitoring.

## Backup & restore

With an external database (the default, e.g. CloudNativePG), use that
database's backups; the chart creates no backup job.

With the bundled database (`db.enabled=true`), the chart runs a nightly
`pg_dump -Fc` CronJob (`backup.enabled`, default `true`):

- with `backup.s3.bucket` set, dumps are uploaded to S3-compatible storage
  (`backup.s3.endpoint`, `backup.s3.existingSecret` with
  `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY`). Set retention with a bucket
  lifecycle rule.
- otherwise they are written to the `<release>-field-tm-backup` PVC and
  pruned after `backup.retentionDays`.

Run a backup now:

```bash
kubectl -n field-tm create job --from=cronjob/field-tm-backup backup-manual
```

Restore a dump (scale the backend down first):

```bash
kubectl -n field-tm scale deploy/field-tm --replicas=0
aws s3 cp s3://my-bucket/field-tm/field-tm-YYYYMMDD-HHMMSS.dump ./restore.dump
pg_restore --clean --if-exists --no-owner \
  -h <db-host> -U fieldtm -d fieldtm ./restore.dump
kubectl -n field-tm scale deploy/field-tm --replicas=1
```

For the PVC, copy the file out with `kubectl cp` from a pod mounting the
backup PVC, or run `pg_restore` from such a pod.

For the deprecated compose stack:

```bash
docker compose -f deploy/compose.sub.yaml exec -T fieldtm-db \
  pg_dump -U fieldtm -Fc fieldtm > field-tm.dump
docker compose -f deploy/compose.sub.yaml exec -T fieldtm-db \
  pg_restore --clean --if-exists --no-owner -U fieldtm -d fieldtm < field-tm.dump
```

## Configuration reference

Set these in the chart's `existingSecret` (or `env`), or in `.env` for
compose.

### Base settings

The `setup` wizard configures these automatically, but you may want to review:

- `DEBUG` (default: `False`): Must be `False` in production
- `LOG_LEVEL` (default: `INFO`): Application log level
  (`DEBUG`, `INFO`, `WARNING`, `ERROR`)
- `FTM_DB_USER` (default: `fieldtm`): PostgreSQL user
- `FTM_DB_NAME` (default: `fieldtm`): PostgreSQL database name
- `FTM_DB_HOST` (default: `fieldtm-db`): Database hostname
  (use default for the compose stack)
- `FTM_API_DOMAIN` (default: `api.$FTM_DOMAIN`): Subdomain for the JSON API
  (optional; defaults to the `api.` prefix)
- `API_REPLICAS` (default: `2`): Number of backend container replicas
- `EXTRA_CORS_ORIGINS` (default: _(empty)_): Comma-separated additional
  allowed CORS origins

### Authentication options

`AUTH_PROVIDER` is required and controls how users sign in:

- `hotosm`: HOT's hosted login at `login.hotosm.org` (HOT deployments only).
  Sets `HANKO_API_URL` and `LOGIN_URL` automatically.
- `bundled`: a self-hosted Hanko; Field-TM serves the login form at `/login`.
  Set `HANKO_API_URL` (backend to Hanko) and `HANKO_PUBLIC_URL` (browser to
  Hanko). With compose, `deploy/compose.login.yaml` runs Hanko and sets both.
- `custom`: your own Hanko plus your own login app. Set `HANKO_API_URL` and
  `LOGIN_URL` (defaults to `$HANKO_API_URL/app`).
- `disabled`: no login, every request is an admin. Local dev only.

Optional OSM account linking (read by hotosm-auth; on when both are set):

- `OSM_CLIENT_ID`, `OSM_CLIENT_SECRET`: OpenStreetMap OAuth2 app
- `OSM_API_URL` (default: `https://www.openstreetmap.org`)
- `OSM_SCOPES` (default: `read_prefs`): space-separated

For the compose Hanko overlay (`AUTH_PROVIDER=bundled`), also set:

- `HANKO_SECRET`: generate with `openssl rand -base64 32`
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`,
  `SMTP_FROM_ADDRESS`: for login passcode emails
- `GOOGLE_ENABLED` (default: `false`), `GOOGLE_CLIENT_ID`,
  `GOOGLE_CLIENT_SECRET`: optional Google sign-in

The overlay derives Hanko's cookie domain, allowed origin and redirect URL
from `FTM_DOMAIN`, and serves Hanko at `login.$FTM_DOMAIN`.

### ODK Central configuration

Field-TM expects an ODK Central account it can use. For external ODK Central,
this user is not created automatically by Field-TM. You must create it on the
ODK Central side and then provide the credentials in `.env`.

- `ODK_CENTRAL_URL` (default: `http://central:8383`): URL of ODK Central
  (use the default for self-hosted deployments)
- `ODK_CENTRAL_USER` (default: `admin@hotosm.org`): ODK Central admin email
- `ODK_CENTRAL_PASSWD` (default: _(dev default)_): ODK Central admin password
- `PYODK_LOG_LEVEL` (default: `CRITICAL`): Log level for the pyodk client
  library

Use either:

- external ODK Central with `just start prod`
- self-hosted ODK Central with `just start prod-with-odk`

If you self-host ODK Central, Field-TM can run the service as part of the
compose stack, but the application still depends on valid ODK credentials in
`.env`.

Self-hosted ODK Central also uses:

- `FTM_ODK_DOMAIN` (default: `odk.$FTM_DOMAIN`): Subdomain for the ODK
  Central web UI
- `CENTRAL_DB_HOST` (default: `central-db`): ODK Central database host
- `CENTRAL_DB_USER` (default: `odk`): ODK Central database user
- `CENTRAL_DB_PASSWORD` (default: `odk`): ODK Central database password
- `CENTRAL_DB_NAME` (default: `odk`): ODK Central database name

### QFieldCloud configuration

Field-TM expects a QFieldCloud account it can use. For external QFieldCloud,
this user is not created automatically by Field-TM. You must create it in
QFieldCloud first, then provide the credentials in `.env`.

- `QFIELDCLOUD_URL` (default: `http://qfield-app:8000`): QFieldCloud server
  URL
- `QFIELDCLOUD_USER` (default: `svcftm`): QFieldCloud service account username
- `QFIELDCLOUD_PASSWORD` (default: _(dev default)_): QFieldCloud service
  account password
- `QFIELDCLOUD_PROJECT_OWNER` (default: `HOTOSM`): Organization owning
  QFieldCloud projects
- `QFIELDCLOUD_QGIS_URL` (default: `http://qfield-qgis:8080`): URL of the QGIS
  wrapper service
- `QFIELDCLOUD_TAG` (default: `26.3`): Image tag for the QGIS wrapper
  container
- `QGIS_LOG_LEVEL` (default: `INFO`): Log level for the QGIS wrapper

### Monitoring options

Monitoring is optional. To enable it, set:

| Variable     | Description               |
| ------------ | ------------------------- |
| `MONITORING` | `openobserve` or `sentry` |

For OpenObserve, also set:

- `OPENOBSERVE_USER` (default: `admin@hotosm.org`): OpenObserve admin user
- `OPENOBSERVE_PASSWORD` (default: _(dev default)_): OpenObserve admin
  password
- `OPENOBSERVE_RETENTION_DAYS` (default: `90`): Log retention in days
- `OTEL_ENDPOINT` (default: _(empty)_): OpenTelemetry collector endpoint
- `OTEL_AUTH_TOKEN` (default: _(empty)_): OpenTelemetry auth token

For Sentry, set:

- `SENTRY_DSN`: Sentry DSN for error reporting

### Other useful options

- `RAW_DATA_API_URL` (default: `https://api-prod.raw-data.hotosm.org/v1`):
  Override the default raw-data-api endpoint
- `RAW_DATA_API_AUTH_TOKEN` (default: _(empty)_): Token for the raw-data-api,
  if required

## Docker Compose (deprecated)

Compose deployments are community-supported. New deployments should use Helm.

The stack is:

- core deployment from `deploy/compose.sub.yaml`
- optional self-hosted ODK overlay from `deploy/compose.odk.yaml`
- optional self-hosted Hanko overlay from `deploy/compose.login.yaml`

The `install.sh` flow is deprecated and should not be used.

### Recommended host

- Ubuntu Linux
- a non-root user with `sudo`
- a DNS record pointing your domain to the server

### 1. Clone the repo

```bash
git clone https://github.com/hotosm/field-tm.git
cd field-tm
```

You do not need to check out a release tag manually.
`just start prod` will prompt you to select a version interactively.

### 2. Prepare the machine

```bash
just prep machine
```

Run this as a non-root user. It installs and configures the container runtime
(runc, containerd, nerdctl) in rootless mode.

### 3. Configure `.env`

```bash
just config setup
```

This runs an interactive wizard that:

1. Generates `.env` from `.env.example`
2. Asks for your domain and Let's Encrypt email
3. Lets you choose an auth provider
4. Auto-generates secure secrets and database passwords
5. Pauses so you can review and edit `.env` before continuing

For advanced or automated setups you can instead run
`just config generate-dotenv` and edit `.env` by hand. See the
[configuration reference](#configuration-reference) for all variables.

### 4. Deploy

#### Core Field-TM

Use this when ODK Central and QFieldCloud are managed outside this stack.

```bash
just start prod
```

#### Field-TM with self-hosted ODK Central

```bash
just start prod-with-odk
```

#### Field-TM with self-hosted Hanko login

Set `AUTH_PROVIDER=bundled` in `.env` (or select it during `just config setup`),
then run `just start prod` - the login overlay is included automatically.

All commands will:

1. Check for uncommitted changes (and refuse to proceed if dirty)
2. Present a numbered list of available release versions
3. Check out the selected tag
4. Generate `.env` if missing
5. Deploy the compose stack

### 5. Verify

After deployment:

- open `https://<your-domain>`
- confirm the homepage loads
- if auth is enabled, confirm sign-in works
- inspect running containers with `docker compose ps`
- inspect logs with `docker compose logs backend`

### Upgrading

To upgrade to a newer release:

```bash
cd field-tm
git fetch --tags
just start prod
```

Select the new version from the menu. Your `.env` is preserved between
upgrades. If a new release adds env vars, check `.env.example` for new
entries and add them to your `.env`.

### Compose files

- `deploy/compose.sub.yaml`: core Field-TM, PostgreSQL, BunkerWeb, QGIS wrapper
- `deploy/compose.odk.yaml`: adds self-hosted ODK Central
- `deploy/compose.login.yaml`: adds self-hosted Hanko login

Do not run `docker compose` directly against `deploy/compose.sub.yaml` without
preprocessing. It uses `${FTM_DOMAIN}` in environment key names, so it must go
through `envsubst`. The `just start prod*` commands handle this correctly.

### Help, Field-TM is broken

Production issues usually fall into a few categories. Work through these steps
in order.

#### Check the containers are running

```bash
docker compose -f deploy/compose.sub.yaml ps
```

All services should show `Up` or `healthy`. If a service is restarting or
exited, check its logs:

```bash
docker compose -f deploy/compose.sub.yaml logs <service-name>
```

Replace `<service-name>` with `backend`, `proxy`, `fieldtm-db`, `migrations`,
`qfield-qgis`, or `dns`.

#### Backend won't start

- Check `docker compose -f deploy/compose.sub.yaml logs backend` for Python
  tracebacks.
- Common cause: missing or wrong env vars in `.env`. Compare your `.env`
  against `.env.example` for new or renamed variables.
- If the `migrations` service failed, the backend will not start. Check
  `docker compose -f deploy/compose.sub.yaml logs migrations` for SQL errors.

#### HTTPS / Let's Encrypt issues

- BunkerWeb handles TLS automatically. If the site loads on HTTP but not HTTPS,
  check the proxy logs:
  `docker compose -f deploy/compose.sub.yaml logs proxy`
- Ensure `FTM_DOMAIN` and `CERT_EMAIL` are set correctly in `.env`.
- Let's Encrypt has rate limits. If you've hit them, wait and retry later.
  During testing, uncomment `USE_LETS_ENCRYPT_STAGING: yes` in
  `deploy/compose.sub.yaml`.

#### DNS resolution failures inside containers

The production stack uses a custom dnsmasq container (`dns`) because
nerdctl/containerd doesn't resolve container names the same way Docker does.
If services can't reach each other:

- Verify the `dns` container is healthy:
  `docker compose -f deploy/compose.sub.yaml logs dns`
- The dns service must start _after_ all other containers are assigned IPs.
  A restart may fix transient issues:
  `docker compose -f deploy/compose.sub.yaml restart dns`

#### Database issues

- Connect directly to check the database is accepting connections:
  `docker compose -f deploy/compose.sub.yaml exec fieldtm-db pg_isready`
- If the volume was deleted or corrupted, data will be lost. The database
  volume is `field-tm-db-data`. Back it up regularly.

#### ODK Central not reachable (self-hosted)

- Check all Central containers are running:
  `docker compose -f deploy/compose.sub.yaml -f deploy/compose.odk.yaml ps`
- Verify `ODK_CENTRAL_URL`, `ODK_CENTRAL_USER`, and `ODK_CENTRAL_PASSWD` in
  `.env` match the Central instance.

#### Restarting everything cleanly

If all else fails, a full recreate (without losing data):

```bash
docker compose -f deploy/compose.sub.yaml down
just start prod
```

This preserves database volumes. To also wipe data and start fresh:

```bash
docker compose -f deploy/compose.sub.yaml down -v
just start prod
```

#### Getting help

- Check the [GitHub issues](https://github.com/hotosm/field-tm/issues) for
  known problems.
- Open a new issue with your error logs if you're stuck.
- Join the [HOT Slack](https://slack.hotosm.org) for community support.

## Notes

- The compose stack exposes ports `80` and `443`.
- The backend API is served by the same LiteStar app as the HTMX manager UI.
