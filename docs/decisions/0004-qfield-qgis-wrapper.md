# Custom QGIS HTTP wrapper for QField project creation

## Context and Problem Statement

Field-TM supports QField as an alternative to ODK for field data collection.
Creating a QField project requires converting an XLSForm + GeoJSON into a
QGIS project file (`.qgz`), then uploading it to QFieldCloud.

We built a lightweight HTTP wrapper around QGIS (`src/qfield/project_gen_svc.py`)
running in a Docker container to handle this conversion. The question arose
whether we could instead use QFieldCloud's built-in jobs system to defer this
responsibility to the QField team and reduce our maintenance burden.
User creation is tracked separately; we are working upstream to add this to the
QFieldCloud API.

## Considered Options

- Use QFieldCloud built-in jobs (via API/SDK)
- Keep the custom QGIS HTTP wrapper as a k8s pod sidecar
- Keep the custom QGIS HTTP wrapper as a separate k8s Deployment

## Decision Outcome

Keep the custom QGIS HTTP wrapper as a **separate Kubernetes Deployment** (not
a sidecar).

### Why not QFieldCloud built-in jobs

QFieldCloud jobs (`process_projectfile`, `package`, `delta_apply`) operate on
an existing QGIS project. They do not create a project from XLSForm + GeoJSON
or support our plugin requirements. We still need our wrapper to generate the
`.qgz`; after upload, QFieldCloud handles its normal validation/packaging jobs.

### Why not a sidecar

Sidecar deployment coupled QGIS scaling to backend scaling and created a
multi-process pod. Running the wrapper as its own Deployment avoids both.

The backend calls the wrapper via `QFIELDCLOUD_QGIS_URL`. Input and output
files are exchanged via the shared PostgreSQL database (see
[0006-db-shared-state-qgis-jobs](0006-db-shared-state-qgis-jobs.md)).

### Concurrency within each QGIS replica

QGIS processing is not thread-safe. The service accepts concurrent requests,
but each replica serializes QGIS work with a `threading.Lock`. Parallelism comes
from replica count (`qfieldQgis.replicaCount`, default `2`).

## Consequences

- Good, because the wrapper is minimal (single file, ~745 lines) on a
  stable base image (`ghcr.io/opengisch/qfieldcloud-qgis`).
- Good, because QFieldCloud's auto-triggered jobs already handle validation
  and packaging after file upload, so we get that for free.
- Good: QGIS generation scales independently of backend replicas.
- Good, because it works with remote QFieldCloud instances (SDK handles
  auth/upload; wrapper runs locally).
- Bad, we maintain a custom Docker container with the XLSFormConverter
  plugin installed.
- Bad, we maintain custom wrapper code/images.

## Future Work

- Move QGIS generation to per-request Kubernetes Jobs to remove persistent QGIS
  pods.
- Contribute upstream support for Kubernetes-backed workers in QFieldCloud.
- Continue upstream collaboration on user-creation API support and adopt it in
  Field-TM when available in released QFieldCloud versions.
