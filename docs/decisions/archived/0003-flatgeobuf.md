# Data extract files should be in flatgeobuf format

## Context and Problem Statement

When creating an Field-TM project, we need a set of geometries to map. This
has typically been called the 'data extract'.

Either the user can upload their own geometries in GeoJSON format, or
download geometries from OSM via a call to raw-data-api.

The resulting data should be easily accessible on the backend for creation of
a matching ODK Entities Dataset (used for the geometry selection in ODK), but
also on the frontend for easy visualisation (ideally without an API call).

A cloud-native format is most appropriate here, to reduce calls to the API,
and outsource to object storage like S3.

## Considered Options

- GeoJSON
- Flatgeobuf
- Geoparquet
- PMTiles (or other vector tiles)

## Decision Outcome

<https://github.com/hotosm/field-tm/pull/1047>

At the time of implementation (Dec 2023), `flatgeobuf` was selected as the best
candidate. The frontend JS implementation is excellent.

- GeoJSON is not cloud native / BBOX accessible via a HTTP RANGE request.
- GeoParquet support on the frontend was lacking.
- PMTile usage was still quite nascent. Since then this has been identified
  as another possible solution. However, creation would require additional libs
  to be bundled in Field-TM, and vector tile styling can be a pain.

Flatgeobuf seems to be most applicable for this use case (a small amount of data).

### Consequences

- Good, because it's a simple format with excellent support in GIS tools (OGR).
- Good, no styling is required. It can be determined by the web library / renderer.
- Good, has built in geospatial index and accepts BBOX-based HTTP RANGE requests.
- Bad, because flatgeobuf does not support compression, so files are marginally
  larger.
