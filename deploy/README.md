# Deployment Config

This directory contains the production-oriented compose files.

Use the `just start prod*` commands from the repo root instead of calling
`docker compose` against these files directly. The production commands handle
the required `envsubst` preprocessing for `${FTM_DOMAIN}`-based environment
keys.

## Compose files

- `compose.sub.yaml`: core Field-TM stack. This includes the backend, database,
  BunkerWeb proxy, and QGIS wrapper. ODK Central and QFieldCloud are expected
  to be external unless you add an overlay.
- `compose.odk.yaml`: optional self-hosted ODK Central overlay.
- `compose.login.yaml`: optional self-hosted Hanko login overlay.
- `compose.qfield.yaml`: reserved for QFieldCloud-related overlays.

## Recommended commands

From the repo root:

```sh
just prep machine
just config setup
just start prod
```

Alternative production entry points:

```sh
just start prod-with-odk
just start prod-login
```
