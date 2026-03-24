# Installation

There are two common ways to get started with Field-TM.

## I want to contribute locally

Use the contributor setup guide:

- [Contributor Setup](https://docs.field.hotosm.org/dev/Setup/)

Short version:

```bash
git clone https://github.com/hotosm/field-tm.git
cd field-tm
just config generate-dotenv
just start dev
```

Open <http://field.localhost:7050>.

## I want to install Field-TM on a server

Use the production deployment guide:

- [Production Deployment](https://docs.field.hotosm.org/dev/Production/)

Short version:

```bash
git clone https://github.com/hotosm/field-tm.git
cd field-tm
just prep machine
just config setup
just start prod
```

`just config setup` walks you through domain, certificates, and auth, then
generates secure secrets automatically. `just start prod` will prompt you to
select a release version, check out that tag, and deploy.

!!! important

        Run `just prep machine` as a non-root user.

## Requirements

For both paths, start with:

- `git`
- `just`
- Docker with the `docker compose` plugin

For backend-only local development, also install `uv`.

## Kubernetes

Deployment via Kubernetes is also supported using the Helm chart.
See [`chart/README.md`](chart/README.md) for details.

## Important notes

- `install.sh` is deprecated and should not be used.
- `.env` is generated from `.env.example`.
- The Docker Compose production path uses the files under `deploy/`.
