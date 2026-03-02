# Custom QGIS HTTP wrapper for QField project creation

## Context and Problem Statement

Field-TM supports QField as an alternative to ODK for field data collection.
Creating a QField project requires converting an XLSForm + GeoJSON into a
QGIS project file (`.qgz`), then uploading it to QFieldCloud.

We built a lightweight HTTP wrapper around QGIS (`src/qfield/project_gen_svc.py`)
running in a Docker container to handle this conversion. The question arose
whether we could instead use QFieldCloud's built-in jobs system to defer this
responsibility to the QField team and reduce our maintenance burden.

## Considered Options

- Use QFieldCloud built-in jobs (via API/SDK)
- Keep the custom QGIS HTTP wrapper

## Decision Outcome

Keep the custom QGIS HTTP wrapper, because QFieldCloud's built-in jobs solve
a fundamentally different problem and cannot replace it.

QFieldCloud exposes exactly three job types via API (`qfieldcloud_sdk`):

- `process_projectfile` - validates an existing `.qgs`/`.qgz` file
- `package` - converts an existing QGIS project to QField offline format
- `delta_apply` - applies sync changes to existing data

None of these create a QGIS project from scratch. They all assume a project
file already exists on QFieldCloud. There is no mechanism for custom job
types, and no way to ensure custom plugins (like XLSFormConverter) are
installed on a remote QFieldCloud instance.

The custom wrapper fills this gap: it takes XLSForm + GeoJSON as input and
produces a `.qgz` project using the XLSFormConverter QGIS plugin. The
generated project is then uploaded to QFieldCloud via the SDK, where
QFieldCloud automatically handles validation (`process_projectfile`) and
packaging (`package`) through its built-in jobs.

This is already a hybrid approach that correctly delegates what can be
delegated while keeping only the necessary custom piece.

### Consequences

- Good, because the wrapper is minimal (single file, ~745 lines) on a
  stable base image (`ghcr.io/opengisch/qfieldcloud-qgis`).
- Good, because QFieldCloud's auto-triggered jobs already handle validation
  and packaging after file upload, so we get that for free.
- Good, because it works with remote QFieldCloud instances (SDK handles
  auth/upload; wrapper runs locally).
- Bad, we maintain a custom Docker container with the XLSFormConverter
  plugin installed.
- Bad, a shared Docker volume couples the wrapper container to the backend.

### Future Simplifications

- The wrapper could potentially run as a one-shot container or subprocess
  instead of a persistent HTTP server.
- If XLSFormConverter gains a headless CLI mode, the wrapper could be
  simplified further.
