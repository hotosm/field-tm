# Use Electric-SQL as a sync layer on mapper-frontend

## Context and Problem Statement

We are transitioning the mapper frontend in FieldTM to a
[local-first](https://localfirstweb.dev)
application state model, where data is stored and queried locally (in the browser)
and synchronized with a remote server in the background.

This shift supports:

- **Offline use**: Field mappers often operate in remote areas with unreliable
  or no connectivity.
- **Responsiveness**: Local queries and updates are significantly faster,
  improving the user experience.
- **Resilience**: Use of modern mechanisms such as CRDTs to resolve conflicts
  in data capture.

We needed a solution to synchronize a PostgreSQL-based backend with a local
client-side database that integrates smoothly into our stack.

## Considered Options

- ElectricSQL
  - Syncs a remote PostgreSQL instance with a local embedded Postgres (pglite)
    in the browser.
  - Offers a strong local-first story, full SQL support, and CRDT-based
    conflict resolution.
  - Developed using Elixir, a language very well optimised for concurrent
    user patterns and
    real-time web capabilities.
  - Also uses standard HTTP instead of Web Sockets, to fully utilise existing
    infrastructure such as proxy caching and load balancing systems.

- Replicache
  - Uses a custom sync engine and local IndexedDB storage. Well-designed for
    reactivity and performance.
  - Not SQL-based—requires writing a custom sync protocol and a client-side
    data model.

- PowerSync
  - Syncs PostgreSQL to SQLite via a WebSocket-based protocol.
  - Lightweight and performant, syncing to SQLite in-browser.
  - Recently open-sourced their sync layer to self-host.
  - Uses MongoDB underneath, which we do not use anywhere at HOT currently
    (we are migrating the usage in OAM to Postgres, due to issues in the
    legacy system). Written in JS.

- Custom sync layer
  - Building our own logic on top of IndexedDB or WebStorage with a REST or
    WebSocket backend.
  - High flexibility, but requires significant engineering effort to match the
    robustness of existing tools.

## Decision Outcome

We chose ElectricSQL as the sync layer for our mapper frontend.

This decision was driven by ElectricSQL's alignment with our technical goals:

- Direct support for PostgreSQL as both the remote and local data model,
  reducing impedance mismatch.
- Ability to run Postgres locally in the browser using pglite, preserving SQL
  semantics and familiar tooling.
- Also has support for many existing extensions, with potential for PostGIS in
  thee future too.
- Built-in CRDT-based conflict resolution, which simplifies eventual consistency
  handling.
- Seamless support for offline-first patterns and live reactivity through sync
  subscriptions.
- Fast-growing open source community and active development. A very strong
  development team behind it (including researchers behind CRDTs).
- While still an emerging tool, ElectricSQL provides the best combination
  of developer ergonomics, architecture fit, and user experience for our
  specific needs.

## Consequences

- ✅ Improved offline support for mappers, with full CRUD capabilities and
  seamless sync once back online.
- ✅ Consistent data model across backend and frontend using SQL, avoiding
  custom client-side stores or abstractions.
- Sharing database init and migration scripts between backend and frontend.
- ✅ Developer familiarity with Postgres tooling and schema migrations,
  even on the frontend.
- ✅ Real-time sync makes the mapper UI more reactive and engaging.
- ❌ Increased bundle size and complexity due to running a Postgres-compatible
  engine in the browser.
- ❌ Limited ecosystem maturity compared to more established tools like
  Replicache or Firebase.
- ❌ Learning curve for the Electric-specific tooling, sync setup, and
  reactive patterns.
- ❌ Not yet battle-tested at massive scale, which could impact confidence
  in long-term durability.
