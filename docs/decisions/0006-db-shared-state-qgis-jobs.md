# Replace shared volume with database for QGIS job file exchange

## Context and Problem Statement

The backend and qfield-qgis containers exchanged input/output files for QGIS
project generation via a shared Docker volume (`/opt/qfield`). This worked for
Docker Compose but required a **ReadWriteMany** PVC in Kubernetes - meaning an
EFS driver, NFS provisioner, or equivalent. That added deployment complexity
and infrastructure cost, especially for self-hosted instances.

## Considered Options

1. **S3 / MinIO object storage** - both containers read/write files via S3 API
2. **PostgreSQL as shared state** - store files in a `qgis_jobs` table
3. **HTTP request/response body** - send input files in the POST body, receive
   output files in the response

## Decision Outcome

**PostgreSQL as shared state** via a `qgis_jobs` table.

### How it works

1. Backend writes input files (XLSForm bytes, features/tasks GeoJSON) to the
   `qgis_jobs` table, keyed by a UUID job ID.
2. Backend POSTs just the `job_id` and processing parameters to the QGIS
   wrapper HTTP service.
3. QGIS wrapper connects to the same database, reads inputs to a local temp
   directory, runs QGIS processing, then writes the output files back to the
   `output_files` JSONB column (as a `{filename: base64_content}` dict).
4. Backend reads the output files from the DB row, writes them to a temp
   directory for QFieldCloud SDK upload, then deletes the row.

### Why not S3

S3 (or MinIO/Garage) would work well but requires users to deploy and configure
an object store. Field-TM aims to be simple to self-host; adding an S3
dependency for a once-a-day operation was not justified.

### Why not HTTP request/response body

Initially implemented but rejected for future-proofing:

- **Memory**: base64-in-JSON loads entire files into memory multiple times.
  A 300 MB mbtiles basemap (planned feature) would cause ~1-1.5 GB peak memory.
- **No resilience**: the HTTP connection stays open for the entire processing
  time. If anything fails, all data must be re-sent from scratch.
- **Not streamable**: `BaseHTTPRequestHandler.rfile.read()` buffers the full
  body.

The DB approach keeps memory flat (reads/writes happen in controlled chunks),
survives container crashes (inputs persist for retry), and scales to larger
files without architectural changes.

### Crash recovery

Rows are short-lived (seconds to minutes) and always deleted by the backend
after processing. If a crash leaves orphaned rows, they can be cleaned up with:

```sql
DELETE FROM qgis_jobs WHERE created_at < NOW() - INTERVAL '1 hour';
```

This can be run on application startup or as a periodic task.

### Future: large basemap files

When basemap support is added (100-300 MB `.mbtiles`), the BYTEA column can be
replaced with PostgreSQL large objects (`lo_create`/`lo_read`/`lo_write`) which
stream in chunks instead of loading the full blob into memory. The current
BYTEA approach works fine for files under ~50 MB.

## Consequences

- Good: eliminates the ReadWriteMany PVC requirement in Kubernetes.
- Good: no new infrastructure - reuses the existing PostgreSQL database.
- Good: crash-resilient - inputs survive container restarts for retry.
- Good: simpler deployment for self-hosted instances.
- Good: HTTP payloads are now tiny (just job ID + parameters).
- Neutral: QGIS container now depends on psycopg (small addition to Dockerfile).
- Neutral: rows are transient and cleaned up immediately; no DB bloat at
  current scale (≤1 project/day).
- Bad: if files grow very large (>500 MB), should migrate to large objects
  for streaming reads/writes.
