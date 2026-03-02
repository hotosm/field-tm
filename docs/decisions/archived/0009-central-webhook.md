# Use a custom webhook to Sync ODK Central submissions to FieldTM

## Context and Problem Statement

We use ODK Central for form delivery and mobile data collection (via ODK Collect),
but our main system (FieldTM) runs a separate Postgres database and does not share
state with ODK Central. In FieldTM, we store a subset of ODK submission data in
order to drive dashboards, analytics, task assignments, and reactive sync through
ElectricSQL.

- ODK Central does not currently offer native webhook support, so there's no
  built-in way to push events (like new submissions) to an external system
  such as FieldTM.
- All current data sharing methods from ODK Central (OData, JSON/CSV APIs,
  XML downloads) are pull-based and require regular polling, which introduces
  latency and resource overhead.

- We needed a push-based solution to keep FieldTM in sync with new ODK submissions
  in near real-time, without relying on polling or shared databases.

## Decision Drivers

- Need for real-time or near-real-time sync from ODK Central to FieldTM.
- Avoiding tight coupling to ODK Central’s internal Postgres schema.
- Preserving the ability to integrate with organization-wide ODK Central instances,
  not just self-hosted ones.
- Future compatibility with other platforms (e.g. Kobo, ona.io) that follow
  ODK standards.
- Supporting local-first and reactive UI through ElectricSQL syncing to a local
  pglite (Postgres in browser) instance.

## Considered Options

1. Polling Central API
   - **Pros**: Supported today; no custom development needed.
   - **Cons**: Inefficient, introduces latency, doesn’t scale well for
     real-time updates.

2. Direct database access
   - **Pros**: Real-time access; no API limitations.
   - **Cons**: Requires FieldTM and Central to be co-deployed; tightly couples
     services and prevents usage with remote/shared instances.

3. Existing middleware/integration tools (e.g. OpenHIM, Zapier, Activepieces)
   - **Pros**: Off-the-shelf options; little code.
   - **Cons**: Complex setup or limited flexibility; often still require polling;
     not a good fit for our lightweight infra.

4. Custom webhook service using ODK audit logs (chosen)
   - **Pros**: Fully decoupled; real-time-ish with small footprint; extendable.
   - **Cons**: Requires ongoing maintenance; relies on parsing Central
     audit logs (not officially a webhook API).

## Decision Outcome

We built central-webhook, a custom lightweight service in Go.

It runs alongside ODK Central and listens for audit events in the database,
using Postgres triggers and NOTIFY to emit changes to an external webhook
endpoint hosted by FieldTM.

## Consequences

- ✅ Push-based updates enable timely sync into FieldTM without polling.
- ✅ Compatible with ElectricSQL, letting us stream changes to the frontend
  instantly.
- ✅ Works with any Central instance, even if hosted by another team or
  organization.
- ✅ Open to supporting other ODK-compatible platforms in the future
  (e.g. Kobo, Ona).
- ✅ Very lightweight and stateless, written in Go and deployable via a small
  container.
- ✅ No dependence on Central internals beyond the audit log, avoiding tight
  coupling.
- ❌ Adds one more moving piece to deploy and monitor.
- ❌ Audit logs were probably not designed for this purpose, but work well for our
  needs.

Future Considerations

- The webhook system may become redundant if we migrate to ODK Web Forms and
  fully integrate form entry directly into FieldTM, bypassing the need for ODK Collect
  and external syncing.
- If ODK Central eventually implements native webhooks, we may retire our custom
  implementation or migrate to the official mechanism if it provides the same flexibility.
- The audit-log parsing strategy is based on a non-public contract, so any major
  changes in Central’s audit structure may require updates to our webhook.
