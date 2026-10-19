<!-- markdownlint-disable MD013 -->

# Field-TM Task Planner

Split an area into mapping tasks, edit them, and assign them to teams. Runs
entirely in the browser (no backend). Output is a [task plan](../../docs/task-plan.md)
GeoJSON file, per-task GPX/GeoJSON, or a share link with a QR code.

## Develop

```bash
pnpm install
pnpm dev        # http://localhost:5173
pnpm test       # vitest (engine tests run PGlite + PostGIS in Node)
pnpm check      # svelte-check
pnpm build      # static site in dist/
SPIKE=1 pnpm vitest run tests/spike.test.ts   # timings, see SPIKE.md
```

AI agents: `.mcp.json` points at the remote Svelte MCP server
(`https://mcp.svelte.dev/mcp`); run its `svelte-autofixer` on components.
Conventions: runes only, `$state.raw` for GeoJSON, logic in plain `.ts`.

## URL parameters

| Params                                  | Mode                                                                                                                                   |
| --------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| none                                    | Standalone: draw/upload an area, download the result                                                                                   |
| `?aoi=<url>&features=<url>&roads=<url>` | Standalone, preloaded from public GeoJSON                                                                                              |
| `?project=<id>`                         | Field-TM: loads `GET /api/v1/projects/{id}/planner-input`, saves with `PUT /api/v1/projects/{id}/task-plan` (same origin, cookie auth) |
| `?project=<id>&view=1`                  | Read-only viewer (for the iframe on the project page)                                                                                  |
| `#task=<base64url GeoJSON>`             | Read-only view of one shared task                                                                                                      |

## Deploy

`dist/` is static and uses relative asset paths (`base: './'`), so it works at
a site root, under any sub-path (GitHub Pages), or at `/planner/` in Field-TM.
Override with `PLANNER_BASE=/x/ pnpm build`. Serve `.wasm` as
`application/wasm` and `*.gz` as-is (no `Content-Encoding`). The build reads
SQL from `../backend/packages/area-splitter/area_splitter/algorithms`, so keep
both directories in the build context.

## Architecture

- `src/lib/taskPlan.ts` task plan types, validation, (de)serialisation.
- `src/lib/engine/` PGlite + PostGIS in a Web Worker, lazy-loaded on first
  split. `splitter.ts` ports `area_splitter/splitter.py`: it loads the AOI and
  data into the same temp tables and runs the backend's SQL files, imported
  with `?raw` (not copied). Grid split is a small SQL port of `splitBySquare`.
- `src/lib/exports.ts`, `share.ts`, `history.ts`, `planEdit.ts`, `draft.ts`
  (localStorage autosave), `io/` (files, Field-TM API, Overpass).
- `src/lib/planner.svelte.ts` reactive state; `src/components/` UI only.
- Basemap: OpenFreeMap. Roads: Overpass API. Buildings: upload, e.g. from
  [export.hotosm.org](https://export.hotosm.org).
- Plain HTML/CSS with HOT red rather than `@hotosm/ui`, to avoid loading the
  web component bundle from a CDN in an offline-friendly static app.

TODO: straight-skeleton splitting (needs SFCGAL, not in PGlite's PostGIS).
