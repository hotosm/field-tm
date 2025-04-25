# Use ParaglideJS for frontend internationalisation (translations)

## Context and Problem Statement

We need to serve Field-TM in many languages, not just English, as mappers are
global.

Ideally these translations are contributed by the **community** and not
just the HOT team.

We will likely ask the community to contribute translations via **Weblate**,
or another similar tool.

We will not consider closed-source / paid tools for this, such as:

- Transifex
- Tolgee (although this looks good!)
- Crowdin

## Considered Options

- Any library that is framework specific, such as **react-i18next**,
  **react-intl**, or **svelte-i18n**. These won't be used to avoid lock-in and
  to aid transfer of translations across projects.
- **i18next** is one of the most prominent, but other tools have
  since superseded this in terms of usability and performance.
- **lingui** looks like an excellent choice, with many nice features
  such as being platform agnostic, good community, and semantic key
  translations (meaning the actual english text to be translated
  is present in the code, instead of a key like home.banner.hello).
- **ParaglideJS** is the newest here, with most of the same advantages of
  lingui, including a few extra such as code splitting / tree shaking.

## Decision Outcome

We chose ParaglideJS for two primary reasons:

- Support for tree shaking of translations. Typically the translations
  for an app are all loaded into the frontend as a large bundle. Paraglide
  works differently, in that the frontend only receives the translations
  that are used on the current page (i.e. are split per component / page).
  This uses advantages provided by the bundler (e.g. Vite) to significantly
  reduce bundle size! It's truly a next generation i18n solution that will
  no doubt be copied by others.

- Some other nice features in the tool ecosystem, such as the 'fink'
  translation editor. This is an interactive GUI for less technical users
  to edit the translations, then push them to Github (without needing to
  understand Git and make changes in the code / files directly).

### Consequences

- Good, because it's the most performant of all the solutions.
- Good, because the DevEx is excellent, being very easy to integrate.
- Good, because the files are simple JSON that is easy to edit.
- Good, because supports any web framework through `paraglide-js` package.
- Good, because there is already a nice wrapper available for simpler
  use with Svelte, so we can get integrating into the mapper frontend easily.
- Good, because non-developers can easily use Fink UI to edit translations.
- Bad, because it's the newest tool here and does not have
  significant testing across many production apps.
- Bad, because it doesn't integrate easily with crowdsource translation
  apps such as Weblate, due to lack of an interchange format like
  gettext PO or XLIFF. This may change in future.
