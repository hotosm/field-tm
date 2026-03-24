# Troubleshooting

## Local development issues

### Containers won't start

Check logs for the failing service:

```bash
docker compose logs backend
docker compose logs central
```

If services fail immediately, regenerate your `.env`:

```bash
rm .env
just config generate-dotenv
just start dev
```

### Backend can't connect to the database

The database host `fieldtm-db` is resolved automatically by docker compose.
If the backend reports connection errors:

- Check the database container is healthy: `docker compose ps fieldtm-db`
- Check database logs: `docker compose logs fieldtm-db`
- If the database was recently recreated, migrations may need to run again.
  Restart the stack: `just stop all && just start dev`

### Environment variable errors

If you see errors like:

```text
pydantic.error_wrappers.ValidationError: 3 validation errors for Settings
OSM_URL
  field required (type=value_error.missing)
```

Your environment variables are not loaded. Either:

- Regenerate `.env`: `just config generate-dotenv`
- Or run via just, which loads `.env` automatically:
  `just start backend-no-docker`

### Package import errors (running without Docker)

We use `uv` to manage dependencies. Make sure you're running inside the
uv-managed environment:

```bash
# Check what packages uv sees
cd src/backend && uv pip list

# Verify a package can be imported
uv run python -c "import litestar"
```

If you get import errors, sync dependencies first:

```bash
cd src/backend && uv sync
```

### OSM fieldwork changes not reflected

The `osm-fieldwork` package is mounted inside the backend container during
local development. After modifying code in `src/backend/packages/osm-fieldwork`,
restart the backend:

```bash
docker compose restart backend
```

## Production issues

For production deployment troubleshooting, see the
[Production Deployment](./Production.md#help-field-tm-is-broken) guide.
