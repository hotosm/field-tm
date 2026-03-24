# Production Deployment

Use this guide if you want to run Field-TM on a server.

There are two supported production paths:

**Docker Compose** (this guide) - for single-server deployments:

- core deployment from `deploy/compose.sub.yaml`
- optional self-hosted ODK overlay from `deploy/compose.odk.yaml`
- optional self-hosted Hanko overlay from `deploy/compose.login.yaml`

**Kubernetes / Helm** - for cluster deployments, see
[`chart/README.md`](../../chart/README.md).

The `install.sh` flow is deprecated and should not be used.

## Recommended host

- Ubuntu Linux
- a non-root user with `sudo`
- a DNS record pointing your domain to the server

## 1. Clone the repo

```bash
git clone https://github.com/hotosm/field-tm.git
cd field-tm
```

You do not need to check out a release tag manually.
`just start prod` will prompt you to select a version interactively.

## 2. Prepare the machine

```bash
just prep machine
```

Run this as a non-root user. It installs and configures the container runtime
(runc, containerd, nerdctl) in rootless mode.

## 3. Generate `.env`

```bash
just config generate-dotenv
```

This creates `.env` from `.env.example` if it does not already exist.

## 4. Configure `.env`

The production behavior is controlled by `.env`. Start with the generated file,
then review the sections below.

### Required base settings

Set these for every production deployment:

- `FTM_DOMAIN`: Public domain for your Field-TM instance
  (for example, `fieldtm.example.com`)
- `CERT_EMAIL`: Email for Let's Encrypt certificate registration
- `FTM_DB_PASSWORD`: PostgreSQL password (change from default)
- `ENCRYPTION_KEY`: App encryption key. Generate with
  `openssl rand -base64 32`

Also review:

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

`AUTH_PROVIDER` controls how users sign in:

- `hotosm`: HOT's hosted login at `login.hotosm.org`
  Deploy with `just start prod`
- `custom`: Your own Hanko instance
  Deploy with `just start prod`
- `bundled`: Self-hosted Hanko via the login overlay
  Deploy with `just start prod-login`

If you use `AUTH_PROVIDER=hotosm`, set:

- `OSM_CLIENT_ID`: OAuth2 client ID from OpenStreetMap
- `OSM_CLIENT_SECRET`: OAuth2 client secret
- `OSM_SECRET_KEY`: Secret key for signing OSM tokens

Optional OSM settings:

- `OSM_URL` (default: `https://www.openstreetmap.org`): OSM server URL
- `OSM_SCOPE` (default: `["read_prefs","send_messages"]`): OAuth2 scopes

If you use `AUTH_PROVIDER=custom`, also set:

- `HANKO_API_URL`: URL of your Hanko instance
- `LOGIN_URL`: _(optional)_ URL of your login UI, if hosted separately

If you use `AUTH_PROVIDER=bundled` (self-hosted Hanko), also review:

- `HANKO_SECRET` (default: _(dev default)_): Secret for Hanko. Generate with
  `openssl rand -base64 32`
- `HANKO_COOKIE_DOMAIN` (default: `field.localhost`): Domain for Hanko
  cookies. Set this to `$FTM_DOMAIN`
- `HANKO_ALLOWED_ORIGIN` (default: `http://field.localhost:7050`): Allowed
  origin for Hanko. Set this to `https://$FTM_DOMAIN`
- `HANKO_REDIRECT_URL` (default: `http://field.localhost:7050`): Redirect URL
  after login. Set this to `https://$FTM_DOMAIN`
- `GOOGLE_ENABLED` (default: `false`): Enable Google OAuth in Hanko
- `GOOGLE_CLIENT_ID` (default: _(empty)_): Google OAuth client ID
- `GOOGLE_CLIENT_SECRET` (default: _(empty)_): Google OAuth client secret

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

## 5. Deploy

### Core Field-TM

Use this when ODK Central and QFieldCloud are managed outside this stack.

```bash
just start prod
```

### Field-TM with self-hosted ODK Central

```bash
just start prod-with-odk
```

### Field-TM with self-hosted Hanko login

```bash
just start prod-login
```

All three commands will:

1. Check for uncommitted changes (and refuse to proceed if dirty)
2. Present a numbered list of available release versions
3. Check out the selected tag
4. Generate `.env` if missing
5. Deploy the compose stack

## 6. Verify

After deployment:

- open `https://<your-domain>`
- confirm the homepage loads
- if auth is enabled, confirm sign-in works
- inspect running containers with `docker compose ps`
- inspect logs with `docker compose logs backend`

## Upgrading

To upgrade to a newer release:

```bash
cd field-tm
git fetch --tags
just start prod
```

Select the new version from the menu. Your `.env` is preserved between
upgrades. If a new release adds env vars, check `.env.example` for new
entries and add them to your `.env`.

## Compose files

- `deploy/compose.sub.yaml`: core Field-TM, PostgreSQL, BunkerWeb, QGIS wrapper
- `deploy/compose.odk.yaml`: adds self-hosted ODK Central
- `deploy/compose.login.yaml`: adds self-hosted Hanko login
- `deploy/compose.qfield.yaml`: reserved for QFieldCloud-related overlays

Do not run `docker compose` directly against `deploy/compose.sub.yaml` without
preprocessing. It uses `${FTM_DOMAIN}` in environment key names, so it must go
through `envsubst`. The `just start prod*` commands handle this correctly.

## Help, Field-TM is broken

Production issues usually fall into a few categories. Work through these steps
in order.

### Check the containers are running

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

### Backend won't start

- Check `docker compose -f deploy/compose.sub.yaml logs backend` for Python
  tracebacks.
- Common cause: missing or wrong env vars in `.env`. Compare your `.env`
  against `.env.example` for new or renamed variables.
- If the `migrations` service failed, the backend will not start. Check
  `docker compose -f deploy/compose.sub.yaml logs migrations` for SQL errors.

### HTTPS / Let's Encrypt issues

- BunkerWeb handles TLS automatically. If the site loads on HTTP but not HTTPS,
  check the proxy logs:
  `docker compose -f deploy/compose.sub.yaml logs proxy`
- Ensure `FTM_DOMAIN` and `CERT_EMAIL` are set correctly in `.env`.
- Let's Encrypt has rate limits. If you've hit them, wait and retry later.
  During testing, uncomment `USE_LETS_ENCRYPT_STAGING: yes` in
  `deploy/compose.sub.yaml`.

### DNS resolution failures inside containers

The production stack uses a custom dnsmasq container (`dns`) because
nerdctl/containerd doesn't resolve container names the same way Docker does.
If services can't reach each other:

- Verify the `dns` container is healthy:
  `docker compose -f deploy/compose.sub.yaml logs dns`
- The dns service must start _after_ all other containers are assigned IPs.
  A restart may fix transient issues:
  `docker compose -f deploy/compose.sub.yaml restart dns`

### Database issues

- Connect directly to check the database is accepting connections:
  `docker compose -f deploy/compose.sub.yaml exec fieldtm-db pg_isready`
- If the volume was deleted or corrupted, data will be lost. The database
  volume is `field-tm-db-data`. Back it up regularly.

### ODK Central not reachable (self-hosted)

- Check all Central containers are running:
  `docker compose -f deploy/compose.sub.yaml -f deploy/compose.odk.yaml ps`
- Verify `ODK_CENTRAL_URL`, `ODK_CENTRAL_USER`, and `ODK_CENTRAL_PASSWD` in
  `.env` match the Central instance.

### Restarting everything cleanly

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

### Getting help

- Check the [GitHub issues](https://github.com/hotosm/field-tm/issues) for
  known problems.
- Open a new issue with your error logs if you're stuck.
- Join the [HOT Slack](https://slack.hotosm.org) for community support.

## Notes

- The compose stack exposes ports `80` and `443`.
- The backend API is served by the same LiteStar app as the HTMX manager UI.
