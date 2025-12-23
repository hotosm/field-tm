# Replace FastAPI with LiteStar as backend framework

## Context and Problem Statement

We had a big direction change for FieldTM, see discussions such as:
[https://github.com/hotosm/field-tm/discussions/2945](https://github.com/hotosm/field-tm/discussions/2945)

As part of this, as we want a small and easily maintained frontend, I thought
it would be wise to combine the frontend and backend into a single server.

HTML templating is old-school, but HTMX adds a more modern approach to this,
with a nice user experience provided an good user interactivity.

FastAPI doesn't have HTMX support by default (relying on plugins),
but LiteStar does.

## Considered Options

- LiteStar
- FastAPI

## Decision Outcome

LiteStar has many improvements on FastAPI:

- Built-in HTMX support, no need for external deps to be maintained.
- Great support for server-side rendering and templating.
- Similar design philosophy and API style to FastAPI = easier migration.
- Actively maintained, community-driven, and have good defaults / opinionated.

With the goal of simplifying the stack, it seemed like the right choice.

### Consequences

- ✅ Syntax isn't too different to FastAPI.
- ✅ We can keep using Pydantic / Psycopg combo.
- ✅ Has HTMX support in-built, simplifying the tech stack.
- ✅ No need for SPA frontend project maintenance.
- ❌ Needs work migrating from FastAPI.
- ❌ A small change in skillset for the team, needing to learn
  to use HTMX (small learning curve), instead of SPA frontend.

Overall, trades off some short term migration costs for a
simpler and more maintainable long-term.
