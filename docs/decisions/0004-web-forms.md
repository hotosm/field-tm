# Implement ODK Web Forms to phase out ODK Collect

## Context and Problem Statement

ODK Collect is the mobile survey data collection portion of ODK.

It currently only supports Android.

In FMTM, the mapper is required to swap back-and-forth between the FMTM
and ODK Collect applications, which is not an ideal experience.

Users on iOS also wish to use the FMTM.

## Considered Options

- ODK Collect only
- ODK Collect + GIC Collect (unofficial iOS port)
- ODK Web Forms
- Custom web implementation in FMTM

## Decision Outcome

Between 01-2025 and 05-2025, ODK Web forms will be integrated into FMTM.

Again, we can extend from the excellent work done by ODK on the core
xform-engine logic, then either use their Vue based component implementation
in a Web Component wrapper, or write our own components wrapping this logic.

GIC Collect is closed source and updated infrequently, so not an option.

### Consequences

- Good, because we have to maintain less code ourselves.
- Good, because it broadens the potential user base of FMTM.
- Good, because it simplifies the tech stack for FMTM, with no interfacing
  to an Android application via deep linking / intents required.
- Bad, because it's a risk with Web Forms being such a new project.
- Bad, because it means we are entirely web-based. This has pros and cons,
  but we do lose the benefit of very easy offline submission management
  in ODK Collect (everything required is simply bundled in the app, with
  no web dependencies). We are banking on good caching, intermittent
  connectivity, and a sync layer to facilitate offline-first.
