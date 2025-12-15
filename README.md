<!-- markdownlint-disable -->
<p align="center">
    <!-- github-banner-start -->
    <img src="https://raw.githubusercontent.com/hotosm/field-tm/main/docs/images/hot_logo.png" alt="HOTOSM Logo" width="25%" height="auto" />
    <!-- github-banner-end -->
</p>

<div align="center">
    <h1>Field Tasking Manager (Field-TM)</h1>
    <p>Coordinated field mapping for Open Mapping campaigns.</p>
    <a href="https://github.com/hotosm/field-tm/releases">
        <img src="https://img.shields.io/github/v/release/hotosm/field-tm?logo=github" alt="Release Version" />
    </a>
</div>

</br>

<!-- prettier-ignore-start -->
<div align="center">

| **CI/CD** | | [![Build and Deploy](https://github.com/hotosm/field-tm/actions/workflows/build_and_deploy.yml/badge.svg?branch=main)](https://github.com/hotosm/field-tm/actions/workflows/build_and_deploy.yml?query=branch%3Amain) [![Build CI Img](https://github.com/hotosm/field-tm/actions/workflows/build_ci_img.yml/badge.svg?branch=dev)](https://github.com/hotosm/field-tm/actions/workflows/build_ci_img.yml) [![Build ODK Images](https://github.com/hotosm/field-tm/actions/workflows/build_odk_imgs.yml/badge.svg?branch=dev)](https://github.com/hotosm/field-tm/actions/workflows/build_odk_imgs.yml) <br> [![Publish Docs](https://github.com/hotosm/field-tm/actions/workflows/docs.yml/badge.svg?branch=dev)](https://github.com/hotosm/field-tm/actions/workflows/docs.yml) [![pre-commit.ci](https://results.pre-commit.ci/badge/github/hotosm/field-tm/dev.svg)](https://results.pre-commit.ci/latest/github/hotosm/field-tm/dev) |
| :--- | :--- | :--- |
| **Tech Stack** | | ![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi) ![React](https://img.shields.io/badge/react-%2320232a.svg?style=for-the-badge&logo=react&logoColor=%2361DAFB) ![Svelte](https://img.shields.io/badge/Svelte-4A4A55?style=for-the-badge&logo=svelte) ![Postgres](https://img.shields.io/badge/postgres-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white) ![Kubernetes](https://img.shields.io/badge/kubernetes-%23326ce5.svg?style=for-the-badge&logo=kubernetes&logoColor=white) ![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white) |
| **Code Style** | | [![Backend Style](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/format.json&labelColor=202235)](https://github.com/astral-sh/ruff) [![Frontend Style](https://img.shields.io/badge/code%20style-prettier-F7B93E?logo=Prettier)](https://github.com/prettier/prettier) [![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://results.pre-commit.ci/latest/github/hotosm/field-tm/dev) |
| **Quality** | | [![Coverage](https://docs.field.hotosm.org/coverage.svg)](https://docs.field.hotosm.org/coverage.html) [![Translation](https://hosted.weblate.org/widget/hotosm/field-tm-mapper-ui/svg-badge.svg)](https://hosted.weblate.org/engage/hotosm) [![OpenSSF Best Practices](https://www.bestpractices.dev/projects/9218/badge)](https://www.bestpractices.dev/projects/9218) |
| **Community** | | [![Slack](https://img.shields.io/badge/Slack-Join%20the%20community!-d63f3f?style=for-the-badge&logo=slack&logoColor=d63f3f)](https://slack.hotosm.org) [![All Contributors](https://img.shields.io/github/contributors/hotosm/field-tm?logo=github)](#contributors-) |
| **Other Info** | | [![docs](https://github.com/hotosm/field-tm/blob/dev/docs/images/docs_badge.svg?raw=true)](https://docs.field.hotosm.org/) [![dev-roadmap](https://github.com/hotosm/field-tm/blob/dev/docs/images/dev_roadmap_badge.svg?raw=true)](https://github.com/hotosm/field-tm#roadmap) [![timeline](https://github.com/hotosm/field-tm/blob/dev/docs/images/timeline_badge.svg?raw=true)](https://docs.field.hotosm.org/timeline) [![license-code](https://img.shields.io/github/license/hotosm/field-tm.svg)](https://github.com/hotosm/field-tm/blob/main/LICENSE.md) [![license-translations](https://img.shields.io/badge/license:translations-CC%20BY%204.0-orange.svg)](https://github.com/hotosm/field-tm/blob/main/src/mapper/messages/LICENSE.md) |

</div>

---

<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->

Building on the success of HOT's [Tasking Manager](https://tasks.hotosm.org), a tool
for coordinating remote digitization of map features, the Field-TM was conceived
with the purpose of tagging the features with _field-verified_ information.

While there are many excellent applications for tagging map features already,
the Field-TM aims to solve the problem of **coordinating** field mapping campaigns.

> More details can be found here:
> [overview](https://www.hotosm.org/updates/field-mapping-tasking-manager-fmtm),
> [timeline](https://docs.field.hotosm.org/timeline),
> [docs](https://docs.field.hotosm.org) page, and the
> [FAQ](https://docs.field.hotosm.org/about/faq).

![fmtm-splash][6]

## How Field-TM Works

1. Project is created in an area with three things:
   - Data extract: the features you want to map, say building polygons.
   - ODK XLSForm: the survey for mappers on the ground to fill out for each feature.
   - Task areas divided by feature count and linear features (e.g. rivers, roads).
2. Users assign a task area for themselves, and generate a QR code that is opened
   in ODK Collect.
3. User navigates to the feature and fills out the XLSForm survey, then submits.
4. The submissions are collected by ODK Central, which feeds the data back into
   Field-TM, for cleaning, conflation with existing data, and pushing back to OSM.

## Usage of ODK

This project relies heavily on the [ODK](https://getodk.org) ecosystem underneath:

- [XLSForms](https://xlsform.org) are used for the underlying data collection
  survey. The fields in this survey can be mapped to OpenStreetMap tags.
- [ODK Central](https://github.com/getodk/central) is used to store the XLSForm
  and receive data submissions from users.
- [ODK Collect](https://github.com/getodk/collect) is a mobile app that the user
  submits data from.

## Contributing 👍🎉

In the wake of the 2010 Haiti earthquake, volunteer developers created the
Tasking Manager after seeing a similar coordination challenge for mapping
areas without existing data.

Now with over 500,000 volunteer mappers, the Tasking Manager is a go-to resource
for volunteers to map collaboratively.

To aid future disaster response, we would really welcome contributions for:

- Backend Python development
- Frontend Typescript development
- Documentation writers
- UI / UX designers
- Testers!
- XLSForm creators
- Mobile developers

Please take a look at our [Documentation](https://hotosm.github.io/fmtm)
and [contributor guidance](https://docs.field.hotosm.org/CONTRIBUTING/)
for more details!

Reach out to us if any questions!

## Install

To install for a quick test, or on a production instance,
use the convenience script:

```sh
# Deprecated approach (for now):
# curl --proto '=https' --tlsv1.2 -sSf https://get.field.hotosm.org | bash

# Development
just config generate-dotenv
just start all

# Production
just prep machine
just start prod
```

Alternatively see the [docs](https://docs.field.hotosm.org) for
various deployment guides.

## Roadmap

<!-- prettier-ignore-start -->
| Status | Feature | Release |
| :------: | :-------: | :--------: |
| ✅ | 🖥️ project area splitting avoiding roads, rivers, railways | Since [v2024.4.0][1] |
| ✅ | 🖥️ XLSForm survey generation in ODK Central | Since [v2024.4.0][1] |
| ✅ | 📱 mapping of project via survey in ODK Collect mobile app | Since [v2024.4.0][1] |
| ✅ | 📱 locking & unlocking of tasks to coordinate mapping | Since [v2024.4.0][1] |
| ✅ | 📱 download base imagery & geolocation for in the field | Since [v2024.4.0][1] |
| ✅ | 🖥️ view mapper submissions in the Field-TM dashboard | Since [v2024.4.0][1] |
| ✅ | 📢 Beta Release | Since [v2024.4.0][1] |
| ✅ | 🖥️ & 📱 basic user tutorials and usage guides | Since [v2024.4.0][1] |
| ✅ | 📱 open ODK Collect with feature already selected | Since [v2024.4.0][1] |
| ✅ | 📱 live updates during mapping (if online) | Since [v2024.5.0][2] |
| ✅ | 📱 features turn green once mapped | Since [v2024.5.0][2] |
| ✅ | 📱 navigation and capability for routing to map features | Since [v2024.5.0][2] |
| ✅ | 🖥️ organization creation and management | Since [v2024.5.0][2] |
| ✅ | 📱 better support for mapping **new** points, lines, polygons | Since [v2025.1.0][3] |
| ✅ | 📱 seamless mapping in the same app (Web Forms, no ODK Collect) | Since [v2025.2.0][4] |
| ✅ | 🖥️ user role management per project | Since [v2025.2.0][4] |
| ✅ | 🖥️ inviting users to projects via invite link | Since [v2025.2.0][4] |
| ✅ | 🖥️ optional private projects to restrict access | Since [v2025.2.0][4] |
| ✅ | 📱 fully translated mapper UI and survey in any language | Since [v2025.2.0][4] |
| ✅ | 📱 custom Field-TM deployments with updated branding | Since [v2025.2.0][4] |
| ✅ | 📱 ~~fully offline field mapping (local-first design)~~ | [v2025.3.0][7], [removed][8] |
| 🔄 | 🖥️ integration with QField | – |
| 🔄 | 🖥️ simplify project creation with basic / advanced workflows | – |
| 🔄 | 🖥️ pre-defined OpenStreetMap forms for easy OSM mapping | – |
| 📅 | 🖥️ editing of submissions marked bad by the project manager | – |
| 📅 | 🖥️ reduced resource usage of FieldTM on mobile devices | – |
| 📅 | 🖥️ integration with OSM mobile apps: EveryDoor, StreetComplete | – |
| 📅 | 🖥️ integration with ChatMap | – |
| 📅 | 🖥️ integration with HeiGIT Sketch Map Tool | – |
| 📅 | 🖥️ integration with other ODK server types: Ona.io, Kobo | – |
| 📅 | 🖥️ multiple approaches to task splitting algorithm | – |
| 📅 | 🖥️ improvements to the validation criteria and workflow | – |
| 📅 | 🖥️ export (+merge) the final data to OpenStreetMap | – |
| 📅 | 🖥️ better data visualisation and export options | – |
| 📅 | 🖥️ Field Admin role | – |

<!-- prettier-ignore-end -->

> [!Note]
> 📱 for mobile / mappers
>
> 🖥️ for desktop / managers / validators

## Contributors ✨

Here's how you can contribute:

- [Open an issue](https://github.com/hotosm/field-tm/issues) if you believe you've
  encountered a bug.
- Make a [pull request](https://github.com/hotosm/field-tm/pull) to add new features
  or fix bugs.

Thanks goes to these wonderful people:

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<table>
  <tbody>
    <tr>
      <td align="center" valign="top" width="14.28%"><a href="http://ivangayton.net"><img src="https://avatars.githubusercontent.com/u/5991943?v=4?s=100" width="100px;" alt="Ivan Gayton"/><br /><sub><b>Ivan Gayton</b></sub></a><br /><a href="#projectManagement-ivangayton" title="Project Management">📆</a> <a href="https://github.com/hotosm/field-tm/commits?author=ivangayton" title="Code">💻</a> <a href="https://github.com/hotosm/field-tm/pulls?q=is%3Apr+reviewed-by%3Aivangayton" title="Reviewed Pull Requests">👀</a> <a href="#ideas-ivangayton" title="Ideas, Planning, & Feedback">🤔</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/robsavoye"><img src="https://avatars.githubusercontent.com/u/71342768?v=4?s=100" width="100px;" alt="Rob Savoye"/><br /><sub><b>Rob Savoye</b></sub></a><br /><a href="#maintenance-robsavoye" title="Maintenance">🚧</a> <a href="#mentoring-robsavoye" title="Mentoring">🧑‍🏫</a> <a href="https://github.com/hotosm/field-tm/commits?author=robsavoye" title="Code">💻</a> <a href="https://github.com/hotosm/field-tm/pulls?q=is%3Apr+reviewed-by%3Arobsavoye" title="Reviewed Pull Requests">👀</a> <a href="#ideas-robsavoye" title="Ideas, Planning, & Feedback">🤔</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/ramyaragupathy"><img src="https://avatars.githubusercontent.com/u/12103383?v=4?s=100" width="100px;" alt="Ramya"/><br /><sub><b>Ramya</b></sub></a><br /><a href="https://github.com/hotosm/field-tm/issues?q=author%3Aramyaragupathy" title="Bug reports">🐛</a> <a href="https://github.com/hotosm/field-tm/commits?author=ramyaragupathy" title="Documentation">📖</a> <a href="#ideas-ramyaragupathy" title="Ideas, Planning, & Feedback">🤔</a> <a href="#content-ramyaragupathy" title="Content">🖋</a> <a href="#design-ramyaragupathy" title="Design">🎨</a> <a href="#projectManagement-ramyaragupathy" title="Project Management">📆</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://spwoodcock.dev"><img src="https://avatars.githubusercontent.com/u/78538841?v=4?s=100" width="100px;" alt="Sam"/><br /><sub><b>Sam</b></sub></a><br /><a href="https://github.com/hotosm/field-tm/commits?author=spwoodcock" title="Code">💻</a> <a href="https://github.com/hotosm/field-tm/pulls?q=is%3Apr+reviewed-by%3Aspwoodcock" title="Reviewed Pull Requests">👀</a> <a href="#infra-spwoodcock" title="Infrastructure (Hosting, Build-Tools, etc)">🚇</a> <a href="#ideas-spwoodcock" title="Ideas, Planning, & Feedback">🤔</a> <a href="#maintenance-spwoodcock" title="Maintenance">🚧</a> <a href="#mentoring-spwoodcock" title="Mentoring">🧑‍🏫</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/susmina94"><img src="https://avatars.githubusercontent.com/u/108750444?v=4?s=100" width="100px;" alt="Susmina_Manandhar"/><br /><sub><b>Susmina_Manandhar</b></sub></a><br /><a href="https://github.com/hotosm/field-tm/commits?author=susmina94" title="Documentation">📖</a> <a href="#ideas-susmina94" title="Ideas, Planning, & Feedback">🤔</a> <a href="https://github.com/hotosm/field-tm/issues?q=author%3Asusmina94" title="Bug reports">🐛</a> <a href="#mentoring-susmina94" title="Mentoring">🧑‍🏫</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/manjitapandey"><img src="https://avatars.githubusercontent.com/u/97273021?v=4?s=100" width="100px;" alt="Manjita Pandey"/><br /><sub><b>Manjita Pandey</b></sub></a><br /><a href="https://github.com/hotosm/field-tm/issues?q=author%3Amanjitapandey" title="Bug reports">🐛</a> <a href="https://github.com/hotosm/field-tm/commits?author=manjitapandey" title="Documentation">📖</a> <a href="#ideas-manjitapandey" title="Ideas, Planning, & Feedback">🤔</a> <a href="#content-manjitapandey" title="Content">🖋</a> <a href="#design-manjitapandey" title="Design">🎨</a> <a href="#projectManagement-manjitapandey" title="Project Management">📆</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/Sujanadh"><img src="https://avatars.githubusercontent.com/u/109404840?v=4?s=100" width="100px;" alt="Sujan Adhikari"/><br /><sub><b>Sujan Adhikari</b></sub></a><br /><a href="https://github.com/hotosm/field-tm/commits?author=Sujanadh" title="Code">💻</a> <a href="#maintenance-Sujanadh" title="Maintenance">🚧</a></td>
    </tr>
    <tr>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/NSUWAL123"><img src="https://avatars.githubusercontent.com/u/81785002?v=4?s=100" width="100px;" alt="Nishit Suwal"/><br /><sub><b>Nishit Suwal</b></sub></a><br /><a href="https://github.com/hotosm/field-tm/commits?author=NSUWAL123" title="Code">💻</a> <a href="#maintenance-NSUWAL123" title="Maintenance">🚧</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/varun2948"><img src="https://avatars.githubusercontent.com/u/37866666?v=4?s=100" width="100px;" alt="Deepak Pradhan (Varun)"/><br /><sub><b>Deepak Pradhan (Varun)</b></sub></a><br /><a href="https://github.com/hotosm/field-tm/commits?author=varun2948" title="Code">💻</a> <a href="#ideas-varun2948" title="Ideas, Planning, & Feedback">🤔</a> <a href="#maintenance-varun2948" title="Maintenance">🚧</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/nrjadkry"><img src="https://avatars.githubusercontent.com/u/41701707?v=4?s=100" width="100px;" alt="Niraj Adhikari"/><br /><sub><b>Niraj Adhikari</b></sub></a><br /><a href="https://github.com/hotosm/field-tm/commits?author=nrjadkry" title="Code">💻</a> <a href="#ideas-nrjadkry" title="Ideas, Planning, & Feedback">🤔</a> <a href="#maintenance-nrjadkry" title="Maintenance">🚧</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/krtonga"><img src="https://avatars.githubusercontent.com/u/7307817?v=4?s=100" width="100px;" alt="krtonga"/><br /><sub><b>krtonga</b></sub></a><br /><a href="https://github.com/hotosm/field-tm/commits?author=krtonga" title="Code">💻</a> <a href="https://github.com/hotosm/field-tm/commits?author=krtonga" title="Documentation">📖</a> <a href="#tool-krtonga" title="Tools">🔧</a> <a href="#ideas-krtonga" title="Ideas, Planning, & Feedback">🤔</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://www.hotosm.org/people/petya-kangalova/"><img src="https://avatars.githubusercontent.com/u/98902727?v=4?s=100" width="100px;" alt="Petya "/><br /><sub><b>Petya </b></sub></a><br /><a href="https://github.com/hotosm/field-tm/commits?author=petya-kangalova" title="Documentation">📖</a> <a href="#eventOrganizing-petya-kangalova" title="Event Organizing">📋</a> <a href="#ideas-petya-kangalova" title="Ideas, Planning, & Feedback">🤔</a></td>
      <td align="center" valign="top" width="14.28%"><a href="http://zanrevenue.org"><img src="https://avatars.githubusercontent.com/u/52991565?v=4?s=100" width="100px;" alt="Mohamed Bakari Mohamed"/><br /><sub><b>Mohamed Bakari Mohamed</b></sub></a><br /><a href="https://github.com/hotosm/field-tm/commits?author=Mudi-business" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://www.scdhub.org"><img src="https://avatars.githubusercontent.com/u/4379874?v=4?s=100" width="100px;" alt="G. Willson"/><br /><sub><b>G. Willson</b></sub></a><br /><a href="https://github.com/hotosm/field-tm/commits?author=biomassives" title="Code">💻</a></td>
    </tr>
    <tr>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/JoltCode"><img src="https://avatars.githubusercontent.com/u/46378904?v=4?s=100" width="100px;" alt="JoltCode"/><br /><sub><b>JoltCode</b></sub></a><br /><a href="https://github.com/hotosm/field-tm/commits?author=JoltCode" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/neelimagoogly"><img src="https://avatars.githubusercontent.com/u/97789856?v=4?s=100" width="100px;" alt="Neelima Mohanty"/><br /><sub><b>Neelima Mohanty</b></sub></a><br /><a href="https://github.com/hotosm/field-tm/commits?author=neelimagoogly" title="Documentation">📖</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/Ndacyayisenga-droid"><img src="https://avatars.githubusercontent.com/u/58124613?v=4?s=100" width="100px;" alt="Tayebwa Noah"/><br /><sub><b>Tayebwa Noah</b></sub></a><br /><a href="https://github.com/hotosm/field-tm/commits?author=Ndacyayisenga-droid" title="Documentation">📖</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/mohammadareeb95"><img src="https://avatars.githubusercontent.com/u/77102111?v=4?s=100" width="100px;" alt="Mohammad Areeb"/><br /><sub><b>Mohammad Areeb</b></sub></a><br /><a href="https://github.com/hotosm/field-tm/commits?author=mohammadareeb95" title="Documentation">📖</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/AugustHottie"><img src="https://avatars.githubusercontent.com/u/96122635?v=4?s=100" width="100px;" alt="AugustHottie"/><br /><sub><b>AugustHottie</b></sub></a><br /><a href="https://github.com/hotosm/field-tm/commits?author=AugustHottie" title="Documentation">📖</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/Balofire"><img src="https://avatars.githubusercontent.com/u/102294666?v=4?s=100" width="100px;" alt="Ahmeed Etti-Balogun"/><br /><sub><b>Ahmeed Etti-Balogun</b></sub></a><br /><a href="https://github.com/hotosm/field-tm/commits?author=Balofire" title="Documentation">📖</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/Roseford"><img src="https://avatars.githubusercontent.com/u/75838716?v=4?s=100" width="100px;" alt="Uju"/><br /><sub><b>Uju</b></sub></a><br /><a href="https://github.com/hotosm/field-tm/commits?author=Roseford" title="Documentation">📖</a></td>
    </tr>
    <tr>
      <td align="center" valign="top" width="14.28%"><a href="https://www.el-cordovez.com"><img src="https://avatars.githubusercontent.com/u/75356640?v=4?s=100" width="100px;" alt="JC CorMan"/><br /><sub><b>JC CorMan</b></sub></a><br /><a href="https://github.com/hotosm/field-tm/commits?author=cordovez" title="Documentation">📖</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/Prajwalism"><img src="https://avatars.githubusercontent.com/u/123072058?v=4?s=100" width="100px;" alt="Prajwal Khadgi"/><br /><sub><b>Prajwal Khadgi</b></sub></a><br /><a href="https://github.com/hotosm/field-tm/commits?author=Prajwalism" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/shushila21"><img src="https://avatars.githubusercontent.com/u/77854807?v=4?s=100" width="100px;" alt="shushila21"/><br /><sub><b>shushila21</b></sub></a><br /><a href="https://github.com/hotosm/field-tm/commits?author=shushila21" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/kshitijrajsharma"><img src="https://avatars.githubusercontent.com/u/36752999?v=4?s=100" width="100px;" alt="Kshitij Raj Sharma"/><br /><sub><b>Kshitij Raj Sharma</b></sub></a><br /><a href="https://github.com/hotosm/field-tm/commits?author=kshitijrajsharma" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/mahesh-naxa"><img src="https://avatars.githubusercontent.com/u/72002075?v=4?s=100" width="100px;" alt="Mahesh-wor 'Invoron'"/><br /><sub><b>Mahesh-wor 'Invoron'</b></sub></a><br /><a href="#infra-mahesh-naxa" title="Infrastructure (Hosting, Build-Tools, etc)">🚇</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/azharcodeit"><img src="https://avatars.githubusercontent.com/u/31756707?v=4?s=100" width="100px;" alt="Azhar Ismagulova"/><br /><sub><b>Azhar Ismagulova</b></sub></a><br /><a href="https://github.com/hotosm/field-tm/commits?author=azharcodeit" title="Code">💻</a> <a href="https://github.com/hotosm/field-tm/commits?author=azharcodeit" title="Tests">⚠️</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/synneolsen"><img src="https://avatars.githubusercontent.com/u/107098623?v=4?s=100" width="100px;" alt="synneolsen"/><br /><sub><b>synneolsen</b></sub></a><br /><a href="#ideas-synneolsen" title="Ideas, Planning, & Feedback">🤔</a></td>
    </tr>
    <tr>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/Freedisch"><img src="https://avatars.githubusercontent.com/u/82499435?v=4?s=100" width="100px;" alt="Freedisch"/><br /><sub><b>Freedisch</b></sub></a><br /><a href="https://github.com/hotosm/field-tm/commits?author=Freedisch" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/prasidha1"><img src="https://avatars.githubusercontent.com/u/32433336?v=4?s=100" width="100px;" alt="prasidha1"/><br /><sub><b>prasidha1</b></sub></a><br /><a href="https://github.com/hotosm/field-tm/commits?author=prasidha1" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/iamrajbhattarai"><img src="https://avatars.githubusercontent.com/u/75742784?v=4?s=100" width="100px;" alt="Raj Bhattarai"/><br /><sub><b>Raj Bhattarai</b></sub></a><br /><a href="https://github.com/hotosm/field-tm/commits?author=iamrajbhattarai" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/sijandh35"><img src="https://avatars.githubusercontent.com/u/29759582?v=4?s=100" width="100px;" alt="Sijan Dhungana"/><br /><sub><b>Sijan Dhungana</b></sub></a><br /><a href="https://github.com/hotosm/field-tm/commits?author=sijandh35" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/khushishikhu"><img src="https://avatars.githubusercontent.com/u/65439761?v=4?s=100" width="100px;" alt="Khushi Gautam"/><br /><sub><b>Khushi Gautam</b></sub></a><br /><a href="https://github.com/hotosm/field-tm/commits?author=khushishikhu" title="Documentation">📖</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/Seckrel"><img src="https://avatars.githubusercontent.com/u/43112525?v=4?s=100" width="100px;" alt="Aayam Ojha"/><br /><sub><b>Aayam Ojha</b></sub></a><br /><a href="https://github.com/hotosm/field-tm/commits?author=Seckrel" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/casdal"><img src="https://avatars.githubusercontent.com/u/141283367?v=4?s=100" width="100px;" alt="casdal"/><br /><sub><b>casdal</b></sub></a><br /><a href="https://github.com/hotosm/field-tm/commits?author=casdal" title="Code">💻</a></td>
    </tr>
    <tr>
      <td align="center" valign="top" width="14.28%"><a href="http://danieljdufour.com"><img src="https://avatars.githubusercontent.com/u/4313463?v=4?s=100" width="100px;" alt="Daniel J. Dufour"/><br /><sub><b>Daniel J. Dufour</b></sub></a><br /><a href="#ideas-DanielJDufour" title="Ideas, Planning, & Feedback">🤔</a> <a href="https://github.com/hotosm/field-tm/commits?author=DanielJDufour" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/Joshua-Tihabwangye"><img src="https://avatars.githubusercontent.com/u/143622860?v=4?s=100" width="100px;" alt="Joshua-T-Walker"/><br /><sub><b>Joshua-T-Walker</b></sub></a><br /><a href="https://github.com/hotosm/field-tm/commits?author=Joshua-Tihabwangye" title="Documentation">📖</a></td>
      <td align="center" valign="top" width="14.28%"><a href="http://mapconcierge.com"><img src="https://avatars.githubusercontent.com/u/416977?v=4?s=100" width="100px;" alt="Taichi FURUHASHI"/><br /><sub><b>Taichi FURUHASHI</b></sub></a><br /><a href="#translation-mapconcierge" title="Translation">🌍</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/ajvs"><img src="https://avatars.githubusercontent.com/u/16050172?v=4?s=100" width="100px;" alt="Ajee"/><br /><sub><b>Ajee</b></sub></a><br /><a href="https://github.com/hotosm/field-tm/commits?author=ajvs" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://spotter.ngo"><img src="https://avatars.githubusercontent.com/u/15286128?v=4?s=100" width="100px;" alt="Jiří Podhorecký"/><br /><sub><b>Jiří Podhorecký</b></sub></a><br /><a href="#translation-trendspotter" title="Translation">🌍</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/Anuj-Gupta4"><img src="https://avatars.githubusercontent.com/u/84966248?v=4?s=100" width="100px;" alt="Anuj Gupta"/><br /><sub><b>Anuj Gupta</b></sub></a><br /><a href="https://github.com/hotosm/field-tm/commits?author=Anuj-Gupta4" title="Code">💻</a> <a href="#maintenance-Anuj-Gupta4" title="Maintenance">🚧</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/Sujan167"><img src="https://avatars.githubusercontent.com/u/76505195?v=4?s=100" width="100px;" alt="Sujan Basnet"/><br /><sub><b>Sujan Basnet</b></sub></a><br /><a href="https://github.com/hotosm/field-tm/commits?author=Sujan167" title="Code">💻</a> <a href="#maintenance-Sujan167" title="Maintenance">🚧</a></td>
    </tr>
    <tr>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/Kafle33"><img src="https://avatars.githubusercontent.com/u/121845834?v=4?s=100" width="100px;" alt="Roshan Kafle"/><br /><sub><b>Roshan Kafle</b></sub></a><br /><a href="https://github.com/hotosm/field-tm/commits?author=Kafle33" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://gareth.nz"><img src="https://avatars.githubusercontent.com/u/2064938?v=4?s=100" width="100px;" alt="Gareth Bowen"/><br /><sub><b>Gareth Bowen</b></sub></a><br /><a href="https://github.com/hotosm/field-tm/commits?author=garethbowen" title="Documentation">📖</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/allisonsibrian"><img src="https://avatars.githubusercontent.com/u/114789954?v=4?s=100" width="100px;" alt="allison"/><br /><sub><b>allison</b></sub></a><br /><a href="https://github.com/hotosm/field-tm/commits?author=allisonsibrian" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://amitdkhan-pg.blogspot.com"><img src="https://avatars.githubusercontent.com/u/64206751?v=4?s=100" width="100px;" alt="Amit Khanekar"/><br /><sub><b>Amit Khanekar</b></sub></a><br /><a href="https://github.com/hotosm/field-tm/commits?author=amitdkhan-pg" title="Code">💻</a></td>
    </tr>
  </tbody>
  <tfoot>
    <tr>
      <td align="center" size="13px" colspan="7">
        <img src="https://raw.githubusercontent.com/all-contributors/all-contributors-cli/1b8533af435da9854653492b1327a23a4dbd0a10/assets/logo-small.svg">
          <a href="https://all-contributors.js.org/docs/en/bot/usage">Add your contributions</a>
        </img>
      </td>
    </tr>
  </tfoot>
</table>

<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->

<!-- ALL-CONTRIBUTORS-LIST:END -->

## Repo Activity

![Field-TM Repo Activity][5]

[1]: https://github.com/hotosm/field-tm/releases/tag/2024.4.0 "Beta Release"
[2]: https://github.com/hotosm/field-tm/releases/tag/2024.5.0 "Mapper Frontend"
[3]: https://github.com/hotosm/field-tm/releases/tag/2025.1.0 "New Geoms"
[4]: https://github.com/hotosm/field-tm/releases/tag/2025.2.0 "Web Forms"
[5]: https://repobeats.axiom.co/api/embed/4c670cc740c638c52d6c2e822fe78a999d3994fc.svg "Repobeats analytics image"
[6]: https://raw.githubusercontent.com/hotosm/field-tm/dev/src/mapper/static/screenshot-mapper.jpeg "Mapper Page Screenshot"
[7]: https://github.com/hotosm/field-tm/releases/tag/2025.3.0 "Offline Mode"
[8]: https://github.com/hotosm/field-tm/discussions/2878 "Removed offline support"
