# Deployment Config (deprecated)

> **Deprecated.** Helm (`chart/`) is the only supported production path; see
> `docs/dev/Production.md`. These compose files still work and are kept for
> existing deployments, but are community-supported. `compose.login.yaml` is
> still the recommended way to self-host a Hanko login for any deployment.

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

## Commands

From the repo root:

```sh
just prep machine
just config setup
just start prod            # or: just start prod-with-odk
```

`just start prod` includes the Hanko login overlay when
`AUTH_PROVIDER=bundled` is set in `.env`.
