# Deployment Config

- Docker compose based deployments.
- In production, HOT uses the Kubernetes Helm charts.

## Compose Files

- `compose.sub.yaml`: core FieldTM (API, database, proxy). ODK and QFieldCloud
  are expected to be managed externally - provide their URLs via `.env`.
- `compose.odk.yaml`: optional ODK Central addon overlay. Overlay on top of
  `compose.sub.yaml` when you want to self-host ODK Central:

  ```sh
  envsubst -no-unset -i compose.sub.yaml | \
    docker compose -f - -f compose.odk.yaml up --detach
  ```

- `compose.qfield.yaml`: optional QFieldCloud addon overlay (not yet populated;
  QFieldCloud self-hosting is managed separately).
