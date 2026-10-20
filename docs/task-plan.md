<!-- markdownlint-disable MD013 -->

# Task plan format (v1)

The **task plan** is the only file the Task Planner and the Field-TM manager
exchange. It is plain GeoJSON, so any GIS tool can read it.

```json
{
  "type": "FeatureCollection",
  "task_plan_version": 1,
  "algorithm": "AVG_BUILDING_VORONOI",
  "params": { "num_buildings": 50 },
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Polygon",
        "coordinates": [
          [
            [85.3, 27.71],
            [85.31, 27.71],
            [85.31, 27.72],
            [85.3, 27.71]
          ]
        ]
      },
      "properties": {
        "task_id": 1,
        "assigned_group": "team-a",
        "assigned_to": "Chomba",
        "comment": "Start Monday",
        "colour": "#d63f3f"
      }
    }
  ]
}
```

## Top level

| Key                 | Type   | Notes                                                                                                          |
| ------------------- | ------ | -------------------------------------------------------------------------------------------------------------- |
| `task_plan_version` | int    | Always `1`                                                                                                     |
| `algorithm`         | string | `DIVIDE_BY_SQUARE`, `SPLIT_BY_ROADS`, `AVG_BUILDING_VORONOI`, `AVG_BUILDING_SKELETON`, or `MANUAL` after edits |
| `params`            | object | Parameters used, e.g. `cell_size` (m), `num_buildings` (features per task) or `drop_empty`                     |

## Each feature (one task)

Geometry must be a single `Polygon` (WGS84 lon/lat).

| Property         | Type   | Required | Notes                                                         |
| ---------------- | ------ | -------- | ------------------------------------------------------------- |
| `task_id`        | int    | yes      | `1..n`, unique, no gaps                                       |
| `assigned_group` | string | no       | Team label, letters, digits, `_` and `-` only                 |
| `assigned_to`    | string | no       | Free-text name or username                                    |
| `comment`        | string | no       | e.g. "Assigned to Chomba, start Monday"                       |
| `colour`         | string | no       | `#rrggbb`. Defaults to a colour derived from `assigned_group` |

Readers should ignore unknown properties (the planner may add
`feature_count`, the number of features to map in the task). Empty optional values are omitted.

Reference implementation: `src/planner/src/lib/taskPlan.ts`.

## Field-TM API

- `GET /api/v1/projects/{id}/planner-input`: `{project, aoi, features, task_plan}`.
  Anyone who can view the project; `features` (the data extract) is only
  returned to project managers.
- `PUT /api/v1/projects/{id}/task-plan`: project managers only. Accepts
  `Polygon` or `MultiPolygon` tasks (at most 5000), validates the properties
  above (`assigned_to` up to 100 characters, `comment` up to 500), drops unknown
  properties, stamps missing or duplicate `task_id`s and returns
  `{"task_count": n}`. Errors are `422` with a `detail` message.

The project page also accepts a task plan file upload, using the same
validation.
