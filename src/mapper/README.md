# FMTM Mapper

A standalone mobile UI for the mapper interface.

- First build the image:

```bash
docker compose build ui-mapper
```

> [!NOTE]
> If running this in local development, you may have to clear your
> local database data first (to restart with logical replication).
>
> Run: `docker compose down -v`
>
> to clear the local database data, prior to the commands below.

- Then start the docker compose stack:

```bash
docker compose up -d
```

- The UI runs behind the same Nginx proxy, under the path:

```html
https://DOMAIN/mapnow/{projectId}
```
