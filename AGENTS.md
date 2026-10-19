<!-- markdownlint-disable MD013 MD025 -->

# AGENTS.md

Guidance for AI coding agents in **Field-TM**.
Human developers are accountable for all merged changes.

---

## Project

Field-TM coordinates field mapping campaigns for humanitarian OpenStreetMap
work. Mappers use ODK Collect or QField on mobile; managers create and monitor
projects via a web UI. The backend handles task splitting, ODK/QFieldCloud
integration, data conflation, and submission tracking.

**Stack:** Python 3.13 / LiteStar / HTMX / PostgreSQL 18 + PostGIS 3.6 /
Docker Compose (dev + prod) / Helm (k8s) / uv / Ruff / pre-commit

---

## Structure

```text
src/backend/app/          # LiteStar application
src/backend/app/htmx/     # HTMX routes (server-rendered UI)
src/backend/app/templates/ # Jinja2 templates
src/planner/              # Svelte task planner (pnpm; see its README)
src/backend/app/static/   # Static assets (JS, CSS, images)
src/backend/tests/        # Backend tests
src/backend/packages/     # osm-fieldwork, area-splitter
src/migrations/init/      # Current schema SQL
src/odkcentral/           # ODK Central container config
src/qfield/              # QField container config
docs/decisions/          # MADRs (read before non-trivial changes)
tasks/                   # Just submodule recipes
deploy/                  # Production compose files
chart/                   # Helm chart
```

---

## Commands

```bash
just test backend-routes                   # app tests
just test backend                          # all tests (inc. packages)
just lint                                  # pre-commit hooks
just start dev                             # core docker stack (dev-full: + ODK, QField)
just start backend-no-docker               # backend only (no docker)
just test backend                          # docker test stack
```

---

## Decisions Already Made

Read `docs/decisions/` before proposing alternatives to these:

- **Two apps** (ADR 0007). The **planner** (Svelte 5 + MapLibre + PGlite,
  built with Vite) owns all map editing, with files or the Field-TM API as
  input and output. The **manager** (LiteStar + HTMX) owns storage, forms,
  basemaps, app setup and users. No map editing in HTMX.
- **Migrations.** Fresh schema lives in `src/migrations/init/`; upgrades are
  plain numbered SQL files in `src/migrations/` (keep them, idempotent). No
  Alembic.
- **Rootless containers in prod.** Production uses nerdctl/containerd in
  rootless mode, not Docker daemon. The `just prep machine` flow sets this up.
- **CalVer releases.** Tags are `YYYY.MINOR.PATCH` (e.g. `2026.1.3`), no `v`
  prefix. Conventional Commits for messages.

---

## Where AI Help Is Welcome

- Backend route handlers, services, CRUD logic
- Tests (route/integration tests, unit tests for services)
- HTMX templates and partials
- osm-fieldwork / area-splitter package code
- Documentation and docstrings
- Just task recipes
- Boilerplate, scaffolding, refactoring within existing patterns

---

## Where AI Must Not Act Unsupervised

Get explicit approval before changing:

- Auth/permission model or middleware
- Database schema
- Deployment config (`deploy/`, `chart/`, `.github/workflows/`)
- Dependencies (new or upgraded)
- Encryption, token handling, or credential flows
- CI pipeline configuration

---

## Security Boundaries

Never:

- Commit `.env`, credentials, or secrets
- Hardcode secrets or tokens
- Bypass auth or permission checks
- Use unparameterized SQL or string-interpolated queries
- Use `eval()`, `exec()`, or dynamic code execution
- Introduce XSS vectors (unescaped user input in templates)
- Disable CSRF, CORS, or other security middleware

These are non-negotiable regardless of task scope.

---

## Coding Standards

- Explicit, simple, readable. No unnecessary abstractions.
- Thin route handlers; business logic in `*_services.py` / `*_crud.py`.
- Reuse existing patterns (DTOs, schemas, services) rather than inventing new ones.
- Comments only where intent is non-obvious.
- HTMX: server owns state, use partial responses, no client-side state
  duplication, no JS where HTMX suffices.

### Svelte Patterns

- Svelte 5 runes only (`$state`, `$derived`, `$effect`); no `export let` or stores.
- TypeScript everywhere. Domain logic (task plan, splitting engine, exports,
  undo) in plain `.ts` modules, not components.
- Large GeoJSON in `$state.raw` or pushed straight to MapLibre, not deep `$state`.
- Maps via `svelte-maplibre-gl` (+ `terradraw`, `pmtiles` extensions).
- Use the Svelte MCP server (`npx sv add mcp`, or remote
  `https://mcp.svelte.dev/mcp`); run `svelte-autofixer` on Svelte code until clean.

### HTMX Patterns

- Route handlers should stay thin: parse request, call service/helpers,
  return page or fragment.
- Durable business logic belongs in
  `app.projects.project_services` (or equivalent service modules), not
  template/route glue.
- Prefer `project-setup:*` event names for setup flow HTMX triggers.
- Keep server-rendered state authoritative; use client-side storage only for
  UI convenience.
- For `/api/v1/*` routes, keep the auth posture explicit in code and tests
  (including intentional no-auth endpoints).

---

## Testing Standards

All new behavior must be tested (success + failure paths).

- Route/integration tests for HTTP flows under `src/backend/tests/`.
- Unit tests for isolated service logic as needed.
- Package tests under `src/backend/packages/*/tests/`.
- Do not weaken or delete tests to make CI pass.
- If environment constraints block test execution, state the exact blocker.

---

## Anti-Patterns

- Map-heavy interaction in HTMX + inline JS (use Svelte)
- Svelte for pages that are just forms/lists (use HTMX)
- Large refactors without staged validation
- Mixing old and new architectural styles in one feature
- Duplicating logic between HTMX handlers and API handlers
- Opportunistic dependency upgrades unrelated to the task

---

## Workflow

1. **Discover** - read current code first; prefer existing patterns.
2. **Plan** - minimal, task-scoped edits; identify tests before coding.
3. **Implement** - thin handlers, shared logic, incremental commits.
4. **Verify** - targeted tests first, then broader checks.
5. **Summarize** - changed files, behavioral impact, risks.

## Edit Scope

Default: `src/backend/**`, `src/migrations/init/**`, `docs/**`, `tasks/**`,
`Justfile`

Avoid unless task requires: `src/odkcentral/`, `src/qfield/`

Do not touch without explicit request: `.env`, `chart/`, `deploy/`,
`.github/workflows/`, `**/__pycache__/`, `**/.venv/`

## Commits

Use Conventional Commits. Include a Git trailer:

```text
Assisted-by: <Tool Name>
```

## Done Criteria

1. Behavior implemented and tested.
2. Tests pass (or blockers reported).
3. Lint/format clean for changed scope `prek run --all-files`.
4. File summary and risk notes provided.

When uncertain, ask instead of assuming.

<!-- markdownlint-enable MD013 MD025 -->

---

## Responsible AI Contribution Policy

- Org guidance for AI-assisted contributions: <https://responsibleai.guide>
- Declare the AI assistance level (0-5) in the PR template honestly. Never
  lower the declared level to get a PR reviewed.
- If nobody has read the result, that is level 5: open the PR as a draft.
- Do not work on issues labelled `good first issue` - they exist for humans.
- A human is accountable for every merged change.
