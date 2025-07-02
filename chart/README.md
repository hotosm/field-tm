# HOTOSM Field-TM Chart

Chart for HOTOSM Field Tasking Manager.

## Secrets

Requires secrets to be pre-populated inside the correct namespace:

- Create namespace:

```bash
kubectl create namespace fmtm
kubectl 
```

- **db-fmtm-vars** for postgres database

  - key: FMTM_DB_HOST
  - key: FMTM_DB_USER
  - key: FMTM_DB_PASSWORD
  - key: FMTM_DB_NAME

  ```bash
  kubectl create secret generic db-fmtm-vars --namespace fmtm \
    --from-literal=FMTM_DB_HOST=fmtm-db.fmtm.svc.cluster.local \
    --from-literal=FMTM_DB_USER=xxxxxxx \
    --from-literal=FMTM_DB_PASSWORD=xxxxxxx \
    --from-literal=FMTM_DB_NAME=xxxxxxx
  ```

- **s3-fmtm-vars** for Minio S3

  - key: S3_ENDPOINT
  - key: S3_ACCESS_KEY
  - key: S3_SECRET_KEY
  - key: S3_BUCKET_NAME

  ```bash
  kubectl create secret generic s3-fmtm-vars --namespace fmtm \
    --from-literal=S3_ENDPOINT=fmtm-s3.fmtm.svc.cluster.local \
    --from-literal=S3_ACCESS_KEY=fmtm \
    --from-literal=S3_SECRET_KEY=xxxxxxx \
    --from-literal=S3_BUCKET_NAME=fmtm-data
  ```

- **api-fmtm-vars** for FastAPI

  - key: ENCRYPTION_KEY
  - key: FMTM_DOMAIN
  - key: OSM_CLIENT_ID
  - key: OSM_CLIENT_SECRET
  - key: OSM_SECRET_KEY

  ```bash
  kubectl create secret generic api-fmtm-vars --namespace fmtm \
    --from-literal=ENCRYPTION_KEY=xxxxxxx \
    --from-literal=FMTM_DOMAIN=some.domain.com \
    --from-literal=OSM_CLIENT_ID=xxxxxxx \
    --from-literal=OSM_CLIENT_SECRET=xxxxxxx \
    --from-literal=OSM_SECRET_KEY=xxxxxxx
  ```

## Deployment

```bash
helm upgrade --install fmtm oci://ghcr.io/hotosm/field-tm --namespace fmtm
```

Chart values can be overridden using `values.yaml` or the `--set` flag.

```bash
helm upgrade --install fmtm . \
  --set image.tag=dev \
  --set image.pullPolicy="Always" \
  --set domain="some.new.domain"
```
