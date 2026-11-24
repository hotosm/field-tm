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

The planner already splits, colours and prints tasks with no backend, so it
makes sense to build this once there, and let other tools reuse it.

## Considered Options

- Build team assignment into each tool separately
- Ship the planner as an npm package
- Ship the planner as a container image (chosen)

## Decision Outcome

### Divide among teams

One input (number of teams) and one button. No other options.

1. **Hilliness**: fetch a GLO-30 DEM crop for the area from the HOTOSM
   raster API, and score each task by mean slope. A task is hilly if it's
   above the median _and_ at least 5°. If the DEM fails, everything is flat.
2. **Clusters**: order tasks along a Hilbert curve, then cut the hilly and
   flat tasks into N equal runs each. Team _i_ gets hilly run _i_ and flat
   run _i_, so its two clusters stay close together.
3. **Teams**: named `alpha`, `bravo`, `charlie`... (max 12), each with a
   colour. Hilly tasks get a darker shade. Taken from practices by Sierra Leone team.
4. **Print**: an overview page with the team map and each team's hilly /
   flat task counts.

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

- ✅ Same behaviour in Field-TM, Drone-TM and standalone.
- ✅ Every team gets an equal share of hilly and flat tasks.
- ✅ Frontend-only, no backend APIs needed.
- ✅ Runs standalone for deployments outside of Field-TM + Drone-TM.
- ❌ If all the hills are at one end of the area, each team's two clusters
  end up far apart. We favour fairness over walking distance here.
- ❌ Apps bundling the planner need to bump the pinned version to get fixes.
- ❌ Slightly more complex architecture, for the benefit of having a standalone
  planner module, that others could contribute to.
