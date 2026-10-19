# Web UI Development

Field-TM has two web UIs (see `docs/decisions/0007-svelte-map-ui.md`):

- **Manager site:** server-rendered by LiteStar + HTMX from backend templates.
  Projects, forms, data, app setup, users, sync and exports. No map editing.
- **Task Planner:** a standalone Svelte 5 app in `src/planner/` for splitting,
  editing and assigning tasks in the browser. It is served by the backend at
  `/planner/` and can also be deployed on its own. See `src/planner/README.md`.

## Key Paths

- `src/backend/app/templates/` for page templates
- `src/backend/app/htmx/` for HTMX route handlers
- `src/backend/app/static/` for static assets

## Local Development

Run the core stack (add `dev-odk`, `dev-qfield` or `dev-full` for mapping
app servers):

```bash
just start dev
```

Or run backend only:

```bash
just start backend-no-docker
```

Then open:

- `http://field.localhost:7050` (docker stack), or
- `http://localhost:8000` (backend only)

## Testing

Run backend tests:

```bash
just test backend
```
