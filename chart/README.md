# HOTOSM Field-TM Chart

Chart for HOTOSM Field Tasking Manager.

## Secrets

Requires secrets to be pre-populated inside the correct namespace:

- Create namespace:

```bash
kubectl create namespace field-tm
kubectl 
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
  - key: OSM_SECRET_KEY

  ```bash
  kubectl create secret generic api-ftm-vars --namespace field-tm \
    --from-literal=ENCRYPTION_KEY=xxxxxxx \
    --from-literal=FTM_DOMAIN=some.domain.com \
    --from-literal=OSM_CLIENT_ID=xxxxxxx \
    --from-literal=OSM_CLIENT_SECRET=xxxxxxx \
    --from-literal=OSM_SECRET_KEY=xxxxxxx
  ```

## Bundled Hanko auth

Set `auth.bundled.enabled=true` to deploy a self-hosted Hanko instance (plus
its own in-cluster PostGIS database) alongside field-tm, mirroring
`deploy/compose.login.yaml`. The backend's `HANKO_API_URL` is then pointed at
the in-cluster Hanko service automatically - just make sure `AUTH_PROVIDER`
(the backend default is `bundled`) matches.

`auth.bundled.secret.hankoSecret` is required whenever `auth.bundled.enabled`
is `true` - generate one with `openssl rand -base64 32`. Set
`auth.bundled.config.allowedOrigin`, `cookieDomain` and `redirectUrl` to the
public URL field-tm is served on (defaults are for local dev only).

```bash
helm upgrade --install field-tm . \
  --set auth.bundled.enabled=true \
  --set auth.bundled.secret.hankoSecret="$(openssl rand -base64 32)" \
  --set auth.bundled.config.allowedOrigin=https://field.example.com \
  --set auth.bundled.config.cookieDomain=field.example.com \
  --set auth.bundled.config.redirectUrl=https://field.example.com
```

By default `auth.bundled.db.enabled=true` runs an in-cluster PostGIS database
dedicated to Hanko. Set it to `false` and provide `auth.bundled.db.host` to
point at an external database instead.

This first pass covers the base Hanko `Deployment`/`Service`/config plus its
own database - it does not yet wire up ingress for a public `login.<domain>`
host (see `deploy/compose.login.yaml` for the equivalent reverse-proxy config)
or SMTP/Google OAuth secrets beyond what's exposed under `auth.bundled`.

## Deployment

```bash
helm upgrade --install field-tm oci://ghcr.io/hotosm/field-tm --namespace field-tm
```

By default the chart expects an external database (`db.enabled=false`).
Set `db.enabled=true` to run an in-cluster PostGIS database.
When `db.enabled=false`, provide `FTM_DB_HOST` via your DB secret/env.

Chart values can be overridden using `values.yaml` or the `--set` flag.

```bash
helm upgrade --install field-tm . \
  --set image.tag=dev \
  --set qfieldCloud.tag=26.3 \
  --set image.pullPolicy="Always" \
  --set domain="some.new.domain"
```

## Local cluster override (no ingress)

For local dev clusters (for example Talos), use the included override file:

```bash
helm upgrade --install field-tm ./chart \
  --namespace field-tm \
  --create-namespace \
  -f chart/values.local.yaml
```

This disables ingress, keeps the service as `ClusterIP`, enables bundled PostGIS
(`db.enabled=true`), and sets stricter pod/container security contexts for local
Talos-style `restricted` policies.
It also includes local fallback env vars so `api-ftm-vars` secret creation is optional.
Access the app locally with:

```bash
kubectl -n field-tm port-forward svc/field-tm 8000:8000
```

`values.local.yaml` also overrides backend command/args so the `debug` image
can run in Kubernetes without requiring a `/opt/tests` directory.
