<!-- markdownlint-disable MD013 -->

# Reusable task planner, with fair team assignment

Extends [0007](./0007-svelte-map-ui.md). Used by Drone-TM, see its
[0009](https://github.com/hotosm/drone-tm/blob/dev/docs/decisions/0009-field-tm-splitter.md).

## Context and Problem Statement

Coordinators in both Field-TM and Drone-TM need to divide tasks between
teams, then print a map of who goes where.

Fairness matters: teams walk the ground whether they map or fly, so if we
split by location only, some teams get all the hills (we don't want disgruntled mappers!)

The method below was co-developed with the Sierra Leone field and drone
mapping team, based on how they already divide work between teams.

The planner already splits, colours and prints tasks in the browser, so we
build this once there and let other tools reuse it.

This replaces the [`area-splitter`](../../src/backend/packages/area-splitter)
Python package as our shared splitting tool. Browser splitting is more user
friendly (instant previews, editing on the map), and needs no backend. The
SQL algorithms in `area-splitter` remain the source of truth, compiled into
the planner at build time.

## Considered Options

- Build team assignment into each tool separately
- Ship the planner as an npm package
- Ship the planner as a container image (chosen)

## Decision Outcome

### Divide among teams

One input (number of teams) and one button. No other options.

1. **Hilliness**: ask the HOTOSM raster API for each task's mean slope
   from the GLO-30 DEM. A task is hilly if it's
   above the median _and_ at least 10°. GLO-30 includes buildings and trees, so a flat town still averages 4–6°. If the DEM fails, everything is flat.
2. **Clusters**: order tasks along a Hilbert curve and cut them into 2N
   runs of tasks that share edges (corners don't count). Each team gets two
   runs, one hillier and one flatter, so at most two clusters and no enclaves.
3. **Teams**: named `alpha`, `bravo`, `charlie`... (max 10), each with a
   colour. Hilly tasks get a darker shade.
4. **Print**: an overview page with the team map and each team's hilly /
   flat task counts, then a page per team with only its tasks highlighted.

Tasks gain two optional properties: `slope_deg` and `hilly`.

### URL parameters

The URL decides which tool the planner is working for:

| Params                                  | Used by  | Mode                                              |
| --------------------------------------- | -------- | ------------------------------------------------- |
| none                                    | Anyone   | Draw / upload an area, download the result        |
| `?aoi=<url>&features=<url>&roads=<url>` | Anyone   | Same, preloaded from public GeoJSON               |
| `?fieldtm=<id>`                         | Field-TM | Load and save the project's task plan             |
| `?fieldtm=<id>&view=1`                  | Field-TM | Read-only view, for the project page              |
| `#task=<base64url GeoJSON>`             | Anyone   | Read-only view of one shared task                 |
| `?dronetm=<api>/projects/<id>`          | Drone-TM | Fixed tasks: team assignment and print only (new) |

`&return_to=<url>` adds a back link to the calling app.

In the new Drone-TM mode, the planner reads the project's tasks and no-fly
zones from its public API, then opens straight on team assignment.
Splitting, merging and drawing are disabled, and nothing is saved back.

### Distribution

`ghcr.io/hotosm/field-tm-planner:<version>` is a small nginx image:

- Run it, and you have a website.
- Or bundle it into another app:
  `COPY --from=ghcr.io/hotosm/field-tm-planner:<version> /usr/share/nginx/html <dest>`

The version comes from `src/planner/package.json`, so it releases separately
from Field-TM.

We already publish images to GHCR, and npm wouldn't make local dev any
easier. Either way you point the host app at a local `pnpm build`. We can
still publish an npm package later for non-Docker users, from the same
`dist/`.

### Consequences

- ✅ Same behaviour in Field-TM, Drone-TM and standalone, with no backend.
- ✅ Each team has at most two clusters of touching tasks.
- ❌ Hilly tasks are shared out as evenly as the clusters allow, not
  exactly. Compact clusters come first.
- ❌ A team's two clusters can be far apart.
- ❌ Apps bundling the planner need to bump the pinned version to get fixes.
- ❌ A separate frontend module to maintain, but one others can easily
  contribute to.
