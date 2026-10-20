# HOTOSM Field-TM Chart

Chart for HOTOSM Field Tasking Manager.

## Secrets

Requires secrets to be pre-populated inside the correct namespace:

- Create namespace:

```bash
kubectl create namespace field-tm
```

- **db-ftm-vars** for backend database settings (optional when `db.enabled=true`)

  - key: FTM_DB_HOST
  - key: FTM_DB_USER
  - key: FTM_DB_PASSWORD
  - key: FTM_DB_NAME

  ```bash
  kubectl create secret generic db-ftm-vars --namespace field-tm \
    --from-literal=FTM_DB_HOST=your-db-hostname \
    --from-literal=FTM_DB_USER=xxxxxxx \
    --from-literal=FTM_DB_PASSWORD=xxxxxxx \
    --from-literal=FTM_DB_NAME=xxxxxxx
  ```

- **api-ftm-vars** for the Field-TM backend

  - key: ENCRYPTION_KEY
  - key: FTM_DOMAIN
  - key: OSM_CLIENT_ID
  - key: OSM_CLIENT_SECRET

  ```bash
  kubectl create secret generic api-ftm-vars --namespace field-tm \
    --from-literal=ENCRYPTION_KEY=xxxxxxx \
    --from-literal=FTM_DOMAIN=some.domain.com \
    --from-literal=OSM_CLIENT_ID=xxxxxxx \
    --from-literal=OSM_CLIENT_SECRET=xxxxxxx
  ```

## Auth

The chart does not run Hanko. `auth.provider`:

- `hotosm` (default): the shared HOT login at login.hotosm.org. HOT
  deployments only, as its session cookie is scoped to `hotosm.org`.
- `bundled`: a Hanko you run yourself (same mode as
  `deploy/compose.login.yaml`). Field-TM serves the login form at `/login`.
  Hanko's cookie domain must cover `ingress.host`; see
  `contrib/login/hanko-config.tpl.yaml` for a config template.
- `custom`: your own Hanko plus your own login app (e.g. a fork of
  hotosm/login).
- `disabled`: no login, every request is an admin. Local dev only.

```bash
helm upgrade --install field-tm . \
  --set auth.provider=bundled \
  --set auth.hankoApiUrl=https://login.example.com
```

Use Hanko's public URL: the browser uses it too, and hotosm-auth derives its
cookie domain from it. `custom` also needs `auth.loginUrl`.

## Monitoring

Set `sentry.existingSecret` (a secret with key `SENTRY_DSN`) or `sentry.dsn`
to enable Sentry (`MONITORING=sentry`). Unset means monitoring is off.

## Backups

Only for the bundled database (`db.enabled=true`): a nightly `pg_dump -Fc`
CronJob (`backup.enabled`, default `true`). An external database such as
CloudNativePG manages its own backups, so no CronJob is created.

- With `backup.s3.bucket` set, dumps are uploaded with `aws s3 cp`. Set
  `backup.s3.endpoint` for non-AWS storage and `backup.s3.existingSecret` to a
  secret with `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY`. Use bucket
  lifecycle rules for retention.
- Otherwise dumps go to a PVC (`<release>-field-tm-backup`, kept on uninstall)
  and are deleted after `backup.retentionDays`.

See `docs/dev/Production.md` for restore steps.

## Deployment

```bash
helm upgrade --install field-tm oci://ghcr.io/hotosm/charts/field-tm \
  --namespace field-tm
```

By default the chart expects an external database (`db.enabled=false`, e.g.
CloudNativePG); provide `FTM_DB_*` via `existingSecret`. Set
`db.enabled=true` to run a single in-cluster PostGIS instead.

Field-TM itself needs no object storage (S3). Only QFieldCloud does, and it is
deployed separately.

Chart values can be overridden using `values.yaml` or the `--set` flag.

```bash
helm upgrade --install field-tm . \
  --set image.tag=dev \
  --set qfieldCloud.tag=26.3 \
  --set image.pullPolicy="Always" \
  --set ingress.host="some.new.domain"
```

## Local cluster override (no ingress)

For local dev clusters (for example Talos), use the included override file:

```bash
helm upgrade --install field-tm ./chart \
  --namespace field-tm \
  --create-namespace \
  -f chart/values.local.yaml
```

This disables ingress and auth (`auth.provider=disabled`), keeps the service as
`ClusterIP`, enables bundled PostGIS (`db.enabled=true`), and sets stricter
pod/container security contexts for local Talos-style `restricted` policies.
It also includes local fallback env vars so `api-ftm-vars` secret creation is
optional.
Access the app locally with:

```bash
kubectl -n field-tm port-forward svc/field-tm 8000:8000
```

`values.local.yaml` also overrides backend command/args so the `debug` image
can run in Kubernetes without requiring a `/opt/tests` directory.
