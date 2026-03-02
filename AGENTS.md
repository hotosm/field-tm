# AGENTS.md

Machine-readable operating guidance for AI coding agents in **field-tm**.

Project: **field-tm**  
Accountability: human maintainers are responsible for all merged changes.

---

# 1) Current Architecture (Authoritative)

Field-TM manager workflows currently run through a single LiteStar backend:

- LiteStar app under `src/backend/app/`
- HTMX + server-rendered templates for manager UI
- JSON API routes alongside HTMX routes, with shared backend logic
- Minimal JavaScript only when server-rendering is not enough

Current backend structure to prefer:

- Route layers in `src/backend/app/api/` and `src/backend/app/htmx/`
- Shared business logic in `*_crud.py`, `*_services.py`, helpers, and package code
- Templates and static assets in `src/backend/app/templates/` and `src/backend/app/static/`

Active code and support paths:

- `src/backend/app/`
- `src/backend/tests/`
- `src/backend/packages/osm-fieldwork/`
- `src/backend/packages/area-splitter/`
- `src/migrations/init/`

Supporting local service/container code also exists in:

- `src/odkcentral/`
- `src/qfield/`

Older SQL snapshots live in `src/migrations/archived/` and are not the primary target for schema updates.

---

# 2) Required Reading Order

Before non-trivial changes:

1. `docs/decisions/README.md`
2. Relevant MADR in `docs/decisions/`

Most relevant current architecture decision:

- `docs/decisions/0010-litestar.md`

Note: older decisions under `docs/decisions/archived` should be ignored, and are just historical reference.

---

# 3) Agent Workflow Contract

Use this execution loop:

1. Discover
   - Inspect current code paths first.
   - Prefer existing patterns over inventing new ones.
2. Plan
   - Keep edits minimal and task-scoped.
   - Identify tests to update/add before coding.
3. Implement
   - Keep handlers thin.
   - Put business logic in service/crud layers or package modules.
   - Reuse shared logic across HTMX and API flows.
4. Verify
   - Run targeted tests first, then broader checks.
   - Report what you could and could not verify.
5. Summarize
   - List changed files and behavioral impact.
   - List risks and follow-up actions if any.

For large work, deliver in safe incremental commits/patches rather than one monolith.

---

# 4) Commands (Use These)

Install backend deps:

```bash
cd src/backend && uv sync
```

Run backend app tests:

```bash
cd src/backend && uv run pytest -v tests
```

Run package tests:

```bash
cd src/backend && uv run pytest -v packages/osm-fieldwork/tests packages/area-splitter/tests
```

Run all backend tests from the backend workspace:

```bash
cd src/backend && uv run pytest -v
```

Run lint/format hooks:

```bash
just lint
```

Start full docker stack:

```bash
just start all
```

Run backend-only docker test stack:

```bash
just test backend
```

Run backend without docker:

```bash
just start backend-no-docker
```

---

# 5) Coding Standards

- Prefer explicit, simple, readable code.
- Avoid unnecessary abstractions.
- Keep functions focused and small.
- If there is a well-maintained existing library implementation, use that instead.
- Add comments only where intent is non-obvious.
- Reuse existing DTO/schema/service/crud patterns.
- Keep route handlers thin and move stateful logic into shared backend modules.

HTMX principles:

- Server owns state and rendering decisions.
- Use partial template responses intentionally.
- Avoid client-state duplication.
- Do not add JavaScript where HTMX or server-rendering already covers the flow.

---

# 6) Testing Standards

All new behavior must be tested.

- Cover success and failure paths.
- Favor route/integration behavior tests for HTTP flows.
- Add unit tests for isolated service logic as needed.
- Add backend route tests under `src/backend/tests/`.
- Add package tests under the relevant package directory (`src/backend/packages/*/tests/`).
- Do not weaken/delete tests to "make CI pass".

If environment constraints block test execution, state the exact blocker.

---

# 7) Security and Safety Boundaries

Never:

- Commit `.env` or credentials
- Hardcode secrets/tokens
- Bypass auth/permission checks
- Introduce unparameterized SQL

Ask first before:

- New dependencies
- Auth model changes
- DB schema changes not aligned with current migration strategy
- Deployment/infrastructure changes
- CI workflow changes

---

# 8) Database and Migration Policy

Current schema evolution is expected to be reflected in the base SQL init files under:

- `src/migrations/init/`

Do not add incremental migration files unless explicitly requested by maintainers.
Do not treat `src/migrations/archived/` as the primary place for new schema edits.

---

# 9) Repo Change Boundaries

Default edit scope:

- `src/backend/**`
- `src/migrations/init/**`
- `docs/**`
- `tasks/**` / `Justfile` (only when needed for task alignment)

Usually avoid unless the task explicitly requires it:

- `src/odkcentral/**`
- `src/qfield/**`

Do not modify these unless explicitly requested:

- `.env`
- `chart/`
- `deploy/`
- `.github/workflows/`

Also avoid editing generated or local-environment artifacts unless the task is specifically about them:

- `**/__pycache__/`
- `**/.pytest_cache/`
- `**/.ruff_cache/`
- `src/backend/.venv/`
- `src/backend/dist/`

---

# 10) Dependency and Versioning Policy

- Use Conventional Commits.
- Keep dependency diffs minimal and justified.
- Respect Renovate flow (`renovate.json`).
- Avoid opportunistic upgrades unrelated to the task.

Always include a Git trailer with model information:

```text
Assisted-by: <Tool Name>
```

---

# 11) Anti-Patterns

- Reintroducing SPA patterns for manager workflows
- Adding JS where HTMX/server-rendering is sufficient
- Large refactors without staged validation
- Mixing old and new architectural styles in one feature
- Duplicating business logic between HTMX handlers and JSON API handlers

Consistency and maintainability are higher priority than novelty.

---

# 12) Done Criteria

A change is "done" when all are true:

1. Behavior implemented and documented in code/tests.
2. Relevant tests pass (or blockers are explicitly reported).
3. Lint/format checks run for changed scope.
4. File-level summary and risk notes are provided.

When uncertain, ask instead of assuming.
