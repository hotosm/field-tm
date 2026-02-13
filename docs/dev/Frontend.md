# Web UI Development

Field-TM no longer uses a separate React manager frontend.

The web UI is server-rendered by LiteStar + HTMX from backend templates.

## Key Paths

- `src/backend/app/templates/` for page templates
- `src/backend/app/htmx/` for HTMX route handlers
- `src/backend/app/static/` for static assets

## Local Development

Run the full stack:

```bash
just start all
```

Or run backend only:

```bash
just start backend-no-docker
```

Then open:

- `http://fmtm.localhost:7050` (docker stack), or
- `http://localhost:8000` (backend only)

## Testing

Run backend tests:

```bash
just test backend
```
