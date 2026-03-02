# HOTOSM Field-TM Chart

Chart for HOTOSM Field Tasking Manager.

## Secrets

Requires secrets to be pre-populated inside the correct namespace:

- Create namespace:

```bash
kubectl create namespace field-tm
kubectl 
```

- **db-ftm-vars** for postgres database

  - key: FTM_DB_HOST
  - key: FTM_DB_USER
  - key: FTM_DB_PASSWORD
  - key: FTM_DB_NAME

  ```bash
  kubectl create secret generic db-ftm-vars --namespace field-tm \
    --from-literal=FTM_DB_HOST=fieldtm-db.field-tm.svc.cluster.local \
    --from-literal=FTM_DB_USER=xxxxxxx \
    --from-literal=FTM_DB_PASSWORD=xxxxxxx \
    --from-literal=FTM_DB_NAME=xxxxxxx
  ```

- **api-ftm-vars** for FastAPI

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

## Deployment

```bash
helm upgrade --install field-tm oci://ghcr.io/hotosm/field-tm --namespace field-tm
```

Chart values can be overridden using `values.yaml` or the `--set` flag.

```bash
helm upgrade --install field-tm . \
  --set image.tag=dev \
  --set image.pullPolicy="Always" \
  --set domain="some.new.domain"
```
