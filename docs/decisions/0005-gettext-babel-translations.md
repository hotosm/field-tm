# Use gettext `.po` files with Babel for translations

## Context and Problem Statement

Field-TM needs a translation workflow that works well with the current
LiteStar server-rendered backend, community translation tooling, and the
`osm-fieldwork` package code that is shipped with the backend.

The translation system needs to:

- use a standard interchange format that translators and tooling already know;
- support extraction from Python and template files;
- integrate cleanly with Weblate for community contribution;
- support multiple translation domains where needed;
- avoid custom tooling that is fragile to maintain.

We also considered whether `field-tm` and `osm-fieldwork` translations should
be merged into a single `.po` file. That would only be possible with
significant custom tooling around Babel extraction and update steps.

## Considered Options

- Gettext `.po` catalogs with Babel extraction/update/compile
- JSON-based translation files maintained directly in-repo
- A single shared `.po` catalog containing both `field-tm` and
  `osm-fieldwork` strings
- Separate gettext domains for `field-tm` and `osm-fieldwork`
- Frontend based translation libraries like ParaglideJS (which is great
  but perhaps less applicable here).

## Decision Outcome

We will use gettext `.po` files as the translation format and Babel as the
catalog management tool for extraction, update, and compilation.

We will keep `field-tm` and `osm-fieldwork` as separate gettext domains rather
than forcing both projects into a single shared catalog.

The main reasons are:

- Gettext is the standard format supported broadly across Python web stacks and
  translation platforms.
- `.po` files work natively with Weblate, which matches the goal of community
  translation contribution without custom adapters.
- Babel is the standard Python toolchain for extracting messages from Python
  code and templates and for updating catalogs consistently.
- Source-string based gettext entries are easy for developers to read and
  review in code and translation diffs.
- Separate domains map naturally to the actual code ownership boundary between
  `field-tm` and `osm-fieldwork`.
- Weblate already supports multiple components within one project, so
  translators can work on both domains in one place without us merging the
  catalogs ourselves.
- This keeps the workflow conventional and lowers maintenance risk compared to
  inventing a custom merge pipeline.

### Why not one shared `.po` file

Using one combined catalog for both projects is not feasible without
significant custom tooling.

`pybabel extract` rewrites the generated `.pot` file on each run. There is no
built-in mechanism to preserve manually inserted `osm-fieldwork` entries inside
that generated catalog. To make a single-file design work, we would need a
custom post-extract merge step that re-adds those entries after every
extraction, plus additional safeguards to stop `pybabel update` from marking
them obsolete.

That workflow is fragile, non-standard, and adds maintenance cost without a
meaningful simplification for translators, because Weblate already handles
multiple gettext components natively.

### Consequences

- Good, because gettext `.po` files are a mature and widely understood
  translation format.
- Good, because Babel gives us a standard Python workflow for extract, update,
  and compile operations.
- Good, because Weblate integration is straightforward and does not require
  custom format conversion.
- Good, because separate domains let us keep package and application strings
  organized by source ownership.
- Good, because this approach fits both backend-rendered templates and Python
  application code.
- Bad, because gettext workflows add generated artifacts such as `.pot` and
  compiled catalogs that need to be managed carefully.
- Bad, because translators and developers need to understand domains and the
  extract/update/compile cycle.
- Bad, because strings reused across domains may need duplicate translation
  work if we keep catalogs separate.
- Bad, because translation keying is based on source messages, so changing
  English source text can invalidate existing translations.
