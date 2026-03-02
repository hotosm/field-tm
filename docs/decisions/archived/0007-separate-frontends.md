# Separate frontends for management and mapper experience

## Context and Problem Statement

Initially, FieldTM was implemented as a single backend and frontend application,
serving both managers and mappers through a unified interface.

It became quickly apparent that the needs of our two main user groups—project managers
and field mappers—are significantly different in terms of both UX and technical
constraints.

### Mapper needs

- Mobile-first experience, operated almost exclusively via smartphones.
- Minimal bundle size to accommodate poor network conditions.
- Potential for offline support in the future.
- Focused interaction model: completing mapping tasks efficiently.
- Possibility to use more experiment libraries, such as real-time
  syncing. See the [sync layer](./0008-sync-layer.md) decision.

### Manager needs

- Desktop-first experience, often operated in office or home environments.
- Rich UI with dashboards, task assignment tools, and data overviews.
- Bundle size and performance are less critical.
- No need for offline support.
- More complex workflows, often administrative or supervisory in nature.

## Considered Options

- Single React frontend for all users
  **Pros**: Single codebase to maintain; shared UI components and libraries.
  **Cons**: Difficult to optimize simultaneously for mobile and desktop users;
  risks bloated bundle size and UX compromises for both groups.

- Separate frontends (both in React)
  **Pros**: Clear UX separation, better scoped apps.
  **Cons**: Still carries React's weight for both; redundant logic and tooling.

- Separate frontends with different frameworks
  **Pros**: Allows for framework choice optimized for each use case.
  **Cons**: Increases stack complexity, requires team familiarity with
  multiple frameworks.

- HTMX (or other server-rendered static site) for manager; reactive frontend
  for mapper
  **Pros**: Extremely maintainable for admin interfaces; ideal if React was
  not already in use.
  **Cons**: Costly rewrite; limited interactivity for complex workflows.

## Decision Outcome

We chose to build two separate frontends using different frameworks:

- **Mapper frontend**: Built in Svelte, focusing on a small footprint,
  fast load times, and mobile responsiveness. Svelte’s compilation model
  avoids shipping a large runtime and allows for highly performant UI in
  resource-constrained environments.

- **Manager frontend**: Remains in React, which is familiar to the team and already
  well-established in the project. Although heavier, React’s mature ecosystem and
  component libraries are better suited for building complex administrative dashboards.

This diverges from a previous decision to standardize on
[React](https://docs.hotosm.org/decisions/0003-react), but was necessary
to meet the distinct performance and UX goals for the mapper experience.

We briefly considered switching the manager frontend to HTMX for improved long-term
maintainability, but the rewrite cost was prohibitive. This discussion is
[ongoing](https://github.com/hotosm/field-tm/discussions/1685) and may be revisited.

## Consequences

- ✅ Improved user experience for both mappers and managers, by tailoring each interface
  to its specific audience and device.
- ✅ Significantly smaller bundle size and faster performance for the mapper frontend,
  critical for low-bandwidth field environments.
- ✅ Faster iteration and simpler mental model for mobile app development,
  due to Svelte’s more concise syntax and simpler state handling.
- ✅ Preservation of existing investment in the manager React codebase,
  avoiding unnecessary rewrites.
- ❌ Increased maintenance overhead due to multiple frameworks, requiring the
  team to context-switch between Svelte and React.
- ❌ Shared logic (e.g., form rendering, API clients) must be abstracted into
  framework-agnostic libraries or duplicated, increasing effort.
- ❌ Departure from React-only policy creates inconsistency in the stack and could
  complicate onboarding or developer allocation.
- ❌ Future changes to the manager interface may require difficult tradeoffs if we
  eventually want to transition to something like HTMX or unify frontends.
