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

| **CI/CD** | | [![Build CI Img][badge-build-ci]][10] [![Build ODK Images][badge-build-odk]][11] <br> [![Publish Docs][badge-publish-docs]][12] [![pre-commit.ci][badge-pre-commit-ci]][13] |
| :--- | :--- | :--- |
| **Tech Stack** | | [![Litestar][badge-litestar]][14] [![HTMX][badge-htmx]][15] [![Postgres][badge-postgres]][16] [![Kubernetes][badge-kubernetes]][17] [![Docker][badge-docker]][18] |

| **Code Style** | | [![Backend Style][badge-ruff]][19] [![Prettier][badge-prettier]][20] [![pre-commit][badge-pre-commit]][21] [![uv][badge-uv]][32] |
| **Quality** | | [![Coverage][badge-coverage]][22] [![Translation][badge-translation]][23] [![OpenSSF Best Practices][badge-openssf]][24] |
| **Community** | | [![Slack][badge-slack]][25] [![All Contributors][badge-all-contributors]][26] |
| **Other Info** | | [![docs][badge-docs]][27] [![dev-roadmap][badge-roadmap]][28] [![timeline][badge-timeline]][29] [![license-code][badge-license-code]][30] [![license-translations][badge-license-translations]][31] |

</div>

---

<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->

Building on the success of HOT's [Tasking Manager](https://tasks.hotosm.org), a
tool for coordinating remote digitization of map features, the Field-TM was
conceived with the purpose of tagging the features with _field-verified_
information.

While there are many excellent applications for tagging map features already,
the Field-TM aims to solve the problem of **coordinating** field mapping campaigns.

> [!NOTE]
> More details can be found here:
> [overview](https://www.hotosm.org/updates/field-mapping-tasking-manager-field-tm),
> [timeline](https://docs.field.hotosm.org/timeline),
> [docs](https://docs.field.hotosm.org) page, and the
> [FAQ](https://docs.field.hotosm.org/about/faq).

![field-tm-splash][6]

## How Field-TM Works

1. Project is created in an area with three things:
   - Data extract: the features you want to map, say building polygons.
   - ODK XLSForm: the survey for mappers on the ground to fill out for each feature.
   - Task areas divided by feature count and linear features (e.g. rivers, roads).
2. Users assign a task area for themselves, then map using ODK Collect, ODK Web
   Forms, or QField.
3. User navigates to the feature and fills out the XLSForm survey, then submits.
4. The submissions are collected by ODK Central (or QFieldCloud), which feeds the
   data back into Field-TM, for cleaning, conflation with existing data, and
   pushing back to OSM.

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

- Backend Python development (Litestar + HTMX)
- Documentation writers
- UI / UX designers
- Testers!
- XLSForm creators

Please take a look at our [Documentation](https://hotosm.github.io/field-tm)
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
| ✅ | 🖥️ integration with QField | [v2026.1.0][9] |
| ✅ | 🖥️ multiple approaches to task splitting algorithm | [v2026.1.0][9] |
| 🔄 | 🖥️ pre-defined OpenStreetMap forms for easy OSM mapping | – |
| 📅 | 🖥️ integration with OSM mobile apps: EveryDoor, StreetComplete | – |
| 📅 | 🖥️ integration with ChatMap | – |
| 📅 | 🖥️ integration with HeiGIT Sketch Map Tool | – |
| 📅 | 🖥️ integration with other ODK server types: Ona.io, Kobo | – |
| 📅 | 🖥️ export (+merge) the final data to OpenStreetMap | – |
| 📅 | 🖥️ instructions for how to best visualize ODK data within QField | – |

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
      <td align="center" valign="top" width="14.28%"><a href="http://chainbytes.com"><img src="https://avatars.githubusercontent.com/u/694055?v=4?s=100" width="100px;" alt="Eric Grill"/><br /><sub><b>Eric Grill</b></sub></a><br /><a href="https://github.com/hotosm/field-tm/commits?author=EricGrill" title="Code">💻</a></td>
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

[1]: https://github.com/hotosm/field-tm/releases/tag/2024.4.0 "Beta Release"
[2]: https://github.com/hotosm/field-tm/releases/tag/2024.5.0 "Mapper Frontend"
[3]: https://github.com/hotosm/field-tm/releases/tag/2025.1.0 "New Geoms"
[4]: https://github.com/hotosm/field-tm/releases/tag/2025.2.0 "Web Forms"
[6]: https://raw.githubusercontent.com/hotosm/field-tm/main/src/mapper/static/screenshot-mapper.jpeg "Mapper Page Screenshot"
[7]: https://github.com/hotosm/field-tm/releases/tag/2025.3.0 "Offline Mode"
[8]: https://github.com/hotosm/field-tm/discussions/2878 "Removed offline support"
[9]: https://github.com/hotosm/field-tm/releases/tag/2026.1.0 "Renewed"
[10]: https://github.com/hotosm/field-tm/actions/workflows/build_ci_img.yml "Build CI Img"
[11]: https://github.com/hotosm/field-tm/actions/workflows/build_odk_imgs.yml "Build ODK Images"
[12]: https://github.com/hotosm/field-tm/actions/workflows/docs.yml "Publish Docs"
[13]: https://results.pre-commit.ci/latest/github/hotosm/field-tm/dev "pre-commit.ci"
[14]: https://litestar.dev "Litestar"
[15]: https://htmx.org "HTMX"
[16]: https://www.postgresql.org "PostgreSQL"
[17]: https://kubernetes.io "Kubernetes"
[18]: https://www.docker.com "Docker"
[19]: https://github.com/astral-sh/ruff "Ruff Format"
[20]: https://prettier.io "Prettier"
[21]: https://results.pre-commit.ci/latest/github/hotosm/field-tm/dev "pre-commit"
[22]: https://docs.field.hotosm.org/coverage.html "Coverage Report"
[23]: https://hosted.weblate.org/engage/hotosm "Weblate"
[24]: https://www.bestpractices.dev/projects/9218 "OpenSSF Best Practices"
[25]: https://slack.hotosm.org "HOTOSM Slack"
[26]: #contributors- "All Contributors"
[27]: https://docs.field.hotosm.org/ "Documentation"
[28]: https://github.com/hotosm/field-tm#roadmap "Roadmap"
[29]: https://docs.field.hotosm.org/timeline "Timeline"
[30]: https://github.com/hotosm/field-tm/blob/dev/LICENSE.AGPL-3.0.md "Code License"
[31]: https://github.com/hotosm/field-tm/blob/dev/LICENSE.CC-BY-4.0.md "Translations License"
[32]: https://github.com/astral-sh/uv "uv"
[badge-build-ci]: https://github.com/hotosm/field-tm/actions/workflows/build_ci_img.yml/badge.svg?branch=dev
[badge-build-odk]: https://github.com/hotosm/field-tm/actions/workflows/build_odk_imgs.yml/badge.svg?branch=dev
[badge-publish-docs]: https://github.com/hotosm/field-tm/actions/workflows/docs.yml/badge.svg?branch=dev
[badge-pre-commit-ci]: https://results.pre-commit.ci/badge/github/hotosm/field-tm/dev.svg
[badge-litestar]: https://img.shields.io/badge/Litestar-EDB641?style=for-the-badge&logo=data:image/svg%2Bxml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAzNzUgMzc1Ij48cGF0aCBmaWxsPSJ3aGl0ZSIgZD0iTTEwMS45OSAyNTguMDhjMzQuMzktMS4zNCA3NS4zNi0xMC4wOCAxMTUuNjgtMzUuNzJsLTcuNzcgMjcuNSA0NC45Ny0zNS40MyA0Ny42MyAzMS44MS0xOS44Mi01My43IDQ1LTM1LjQzLTU3LjI1IDIuMjMtMTkuODItNTMuNy0xNS41NiA1NS4wOS01Ny4yNSAyLjI0IDMzLjE0IDIyLjEzYy0yMS44MiAxOS44Mi03Ni41NCA2Mi4xLTE0OS4wMiA2NC45My0xNC42Ni41Ny0zMC4wNC0uNDgtNDYuMDItMy42NSAwIDAgMzYuMDggMTMuNjQgODYuMDYgMTEuNjh6Ii8+PHBhdGggZmlsbD0id2hpdGUiIGQ9Ik0yNTAuNzkgNzguOTdjLTYwLjAxIDAtMTA4LjY1IDQ4LjYtMTA4LjY1IDEwOC41NSAwIDExLjM2IDEuNzUgMjIuMyA0Ljk4IDMyLjU4IDQuNzMtMi4zNSA5LjI0LTQuNzggMTMuNTQtNy4yNi0yLjI3LTguMDUtMy40OC0xNi41NS0zLjQ4LTI1LjMyIDAtNTEuNjUgNDEuOTEtOTMuNTIgOTMuNjEtOTMuNTJzOTMuNiA0MS44NyA5My42IDkzLjUyLTQxLjkxIDkzLjUyLTkzLjYgOTMuNTJjLTI4LjA0IDAtNTMuMTktMTIuMzItNzAuMzUtMzEuODMtNC45OSAxLjk0LTEwLjA0IDMuNzEtMTUuMTUgNS4zIDE5Ljg5IDI1LjMgNTAuNzkgNDEuNTYgODUuNSA0MS41NiA2MCAwIDEwOC42NC00OC42IDEwOC42NC0xMDguNTVzLTQ4LjY0LTEwOC41NS0xMDguNjQtMTA4LjU1eiIvPjxwYXRoIGZpbGw9IndoaXRlIiBkPSJNOTIuMjkgMTczLjAybDUuOTkgMTguNDRoMTkuNGwtMTUuNyAxMS4zOSA2IDE4LjQ0LTE1LjctMTEuMzktMTUuNyAxMS4zOSA2LTE4LjQ0LTE1LjctMTEuMzloMTkuNDF6Ii8+PHBhdGggZmlsbD0id2hpdGUiIGQ9Ik0xMjAuMjEgMTEyLjI1bDUuMTggMTUuOTJoMTYuNzVsLTEzLjU1IDkuODMgNS4xOCAxNS45Mi0xMy41NS05Ljg0LTEzLjU1IDkuODQgNS4xNy0xNS45Mi0xMy41NS05LjgzaDE2Ljc1eiIvPjxwYXRoIGZpbGw9IndoaXRlIiBkPSJNMzQuNyAyMDkuMTRsMy4wMiA5LjI4aDkuNzdsLTcuOTEgNS43NCAzLjAyIDkuMjktNy45LTUuNzQtNy45IDUuNzQgMy4wMi05LjI5LTcuOTEtNS43NGg5Ljc4eiIvPjwvc3ZnPgo=&logoColor=white
[badge-htmx]: https://img.shields.io/badge/HTMX-36C?style=for-the-badge&logo=htmx&logoColor=white
[badge-postgres]: https://img.shields.io/badge/postgres-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white
[badge-kubernetes]: https://img.shields.io/badge/kubernetes-%23326ce5.svg?style=for-the-badge&logo=kubernetes&logoColor=white
[badge-docker]: https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white
[badge-ruff]: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/format.json&labelColor=202235
[badge-prettier]: https://img.shields.io/badge/code_style-prettier-F7B93E?style=for-the-badge&logo=prettier&logoColor=1A2B34
[badge-pre-commit]: https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white
[badge-uv]: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json
[badge-coverage]: https://docs.field.hotosm.org/coverage.svg
[badge-translation]: https://hosted.weblate.org/widget/hotosm/field-tm-mapper-ui/svg-badge.svg
[badge-openssf]: https://www.bestpractices.dev/projects/9218/badge
[badge-slack]: https://img.shields.io/badge/Slack-Join%20the%20community!-d63f3f?style=for-the-badge&logo=slack&logoColor=d63f3f
[badge-all-contributors]: https://img.shields.io/github/contributors/hotosm/field-tm?logo=github
[badge-docs]: https://github.com/hotosm/field-tm/blob/dev/docs/images/docs_badge.svg?raw=true
[badge-roadmap]: https://github.com/hotosm/field-tm/blob/dev/docs/images/dev_roadmap_badge.svg?raw=true
[badge-timeline]: https://github.com/hotosm/field-tm/blob/dev/docs/images/timeline_badge.svg?raw=true
[badge-license-code]: https://img.shields.io/github/license/hotosm/field-tm.svg
[badge-license-translations]: https://img.shields.io/badge/license:translations-CC%20BY%204.0-orange.svg
