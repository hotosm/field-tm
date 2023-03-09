![](images/hot_logo.png)

[![All Contributors](https://img.shields.io/github/all-contributors/hotosm/fmtm?color=ee8449&style=flat-square)](#contributors-)

**Workflows**

[![pytest](https://github.com/hotosm/fmtm/actions/workflows/pytest.yml/badge.svg?branch=main)](https://github.com/hotosm/fmtm/actions/workflows/pytest.yml) [![Publish Docs to Wiki](https://github.com/hotosm/fmtm/actions/workflows/wiki.yml/badge.svg?branch=main)](https://github.com/hotosm/fmtm/actions/workflows/wiki.yml)

**Builds**

**Backend** [![Backend Build](https://quay.io/repository/hotosm/fmtm-backend/status "Backend Build")](https://quay.io/repository/hotosm/fmtm-backend) **ODKCentral-API** [![Central-API Build](https://quay.io/repository/hotosm/odkcentral-api/status "Central-API Build")](https://quay.io/repository/hotosm/odkcentral-api) **ODKCentral-Proxy** [![Central-Proxy Build](https://quay.io/repository/hotosm/odkcentral-proxy/status "Central-Proxy Build")](https://quay.io/repository/hotosm/odkcentral-proxy) **Frontend Main** [![Frontend Main Build](https://quay.io/repository/hotosm/fmtm-mf-main/status "Frontend Main Build")](https://quay.io/repository/hotosm/fmtm-mf-main) **Frontend Map** [![Frontend Map Build](https://quay.io/repository/hotosm/fmtm-mf-map/status "Frontend Map Build")](https://quay.io/repository/hotosm/fmtm-mf-map)

# Field Mapping Tasking Manager (FMTM)

A project to provide tools for Open Mapping campaigns

While we have pretty good field mapping applications, we don’t have great tools to coordinate field mapping. However, we have most of the elements needed to create a field mapping-oriented version of the HOT Tasking Manager, which allows people to select specific areas and complete tasks in a coordinated, organized fashion.

It’s already possible to implement a sort of Field Mapping Tasking Manager workflow using existing tools (mostly based on ODK, particularly the new "select from map" functionality), but it’s pretty labor-intensive and tricky. We’re working on some automation to ease the pain points, which moves us closer to a fully-fledged Field Mapping Tasking Manager (FMTM).

Background and description of the project and idea are here: please have a look at this [blog](https://www.hotosm.org/updates/field-mapping-is-the-future-a-tasking-manager-workflow-using-odk/) if you haven't yet! [Overview, timeline & relevant links](https://docs.google.com/presentation/d/1UrBG1X4MXwVd8Ps498FDlAYvesIailjjPPJfR_B4SUs/edit#slide=id.g15c1f409958_0_0)
for the Field Mapping Tasking Manager (FMTM)

## [side project] FMTM Turkey Earthquake Response Support

Field mapping, especially for damage assessments, is limited by coordination of all the response actors in the affected areas. Yer Çizenler, and OSM community in Turkey, has reported that there is a huge coordination challenge for mapping impacted areas. It is nearly impossible to know what has already been mapped, and duplications and gaps in mapping pose a challenge to building an effective understanding of the impact.

In the wake of the 2010 Haiti earthquake, seeing a similar coordination challenge with mapping affected areas, OSM volunteers developed the Tasking Manager, which allowed mapping volunteers around the world to support building an open-source map of areas without map data. Now with over 500,000 volunteer mappers, the Tasking Manager is a go-to resource for volunteers to contribute to the development of OSM.

HOT is already in the early stages of developing the Field Mapping Tasking Manager (FMTM), but we now need to accelerate this effort and provide a working version for use as soon as possible to the OSM Turkey community and on-the-ground data collectors. We are asking for your developer contributions: calling for 4 developers to work with us on this for 2 weeks See [contributor guidance](https://github.com/hotosm/fmtm/wiki/Contribution) for more detail.

# How to contribute

👍🎉We are actively looking for contributors to this project- from design, user testing and both front and backend developers. We have a specific request for volunteer developers at the moment!
![image](https://user-images.githubusercontent.com/98902727/218812430-3c07b60e-4fd2-4f05-a289-bf37d6f0b9cd.png)
Please take a look at our [Wiki pages](https://github.com/hotosm/fmtm/wiki/Home/90b86d34ddd42f0eafd03ea7e6d443eb37db2df6) and [contributor guidance](https://github.com/hotosm/fmtm/wiki/Contribution) for more details! Reach out to us if any questions! 👍🎉

# Using OpenDataKit's Select From Map feature

As of mid-2022, ODK incorporates a new functionality, select from map, that allows field mappers to select an object from a map, view the existing attributes, and fill out a form adding new information and attributes to that object. For example, a mapper can approach a building, select that building from a map view within ODK on their mobile phone, and add the opening hours, number of floors, construction material, or any number of useful attributes in a well-structured questionnaire format

<img src="https://github.com/hotosm/fmtm/blob/main/images/ODK_Select_one_from_file_map_screenshot.jpg?raw=true"  width=600 height=600>

To prepare the appropriate map files for ODK, we are taking our inspiration from the [HOT Tasking Manager](https://tasks.hotosm.org/), which allows remote mappers to choose well-defined small "task" areas, ensuring full coverage of the project area and no unintended duplication of tasks.

<img src="https://github.com/hotosm/fmtm/blob/main/images/HOT_TM_task_selection_screenshot.jpg?raw=true"  width=600 height=600>

# Users

## Campaign managers

Campaign managers select an Area of Interest (AOI) and organize field mappers to go out and collect data. They need to:

- Select an AOI polygon by creating a GeoJSON or by tracing a polygon in a Web map
- Choose a task division scheme (number of features or area per task, and possibly variations on what features to use as the preferred splitting lines)
- Provide specific instructions and guidance for field mappers on the project.
- Provide a URL to a mobile-friendly Web page where field mappers can, from their mobile phone, select a task that is not already "checked out" (or possibly simply allocate areas to the field mappers).
- See the status of tasks (open, "checked out", completed but not validated, requires rework, validated, etc) in the Web browser on their computer

## Field mappers

Field mappers select (or are allocated) individual tasks within a project AOI and use ODK Collect to gather data in those areas. They need to:

- Visit a mobile-friendly Web page where they can see available tasks on a map
- Choose an area and launch ODK Collect with the form corresponding to their allocated area pre-loaded

## Validators

Validators review the data collected by field mappers and assess its quality. If the data is good, the validators merge the portion of the data that belongs in OpenStreetMap to OSM. If it requires more work, the validators either fix it themselves (for minor stuff like spelling or capitalization mistakes that don't seem to be systematic) or inform the field mappers that they need to fix it. They need to:

- Access completed data sets of "submissions" as Comma Separated Values and/or OSM XML so that they can review it.
- Mark areas as validated or requiring rework
- Communicate with field mappers if rework is necessary
- Merge good-quality data into OSM (probably from JOSM).
- Mark areas as completed and merged.

# Info for developers

The basic setup here is:

## ODK Collect

A mobile data collection tool that functions on almost all Android phones. Field mappers use ODK Collect to select features such as buildings or amenities, and fill out forms with survey questions to collect attributes or data about those features (normally at least some of these attributes are intended to become OSM tags associated with those features).

The ODK Collect app connects to a back-end server (in this case ODK Central), which provides the features to be mapped and the survey form definitions.

## ODK Central server

An ODK Central server which functions as the back end for the field data collectors' ODK Collect apps on their Android phones. Devs must have access to an ODK Central server with a username and password granting admin credentials.

[Here are the instructions for setting up an ODK Central server on Digital Ocean](https://docs.getodk.org/central-install-digital-ocean/) (it's very similar on AWS or whatever)

## Field Mapping Tasking Manager Web App

The FMTM web app is a Python/Flask/Leaflet app that serves as a front end for the ODK Central server, using the [ODK Central API](https://odkcentral.docs.apiary.io/#) to allocate specific areas/features to individual mappers, and receive their data submissions.

### Manager Web Interface (with PC browser-friendlymap view)

A computer-screen-optimized web app that allows Campaign Managers to:

- Select AOIs
- Choose task-splitting schemes
- Provide instructions and guidance specific to the project
- View areas that are at various stages of completion
- Provide a project-specific URL that field mappers can access from their mobile phones to select and map tasks.

### FMTM back end

A back end that converts the project parameters entered by the Campaign Manager in the Manager Web Interface into a corresponding ODK Central project. Its functions include:

- Convert the AOI into a bounding box and corresponding Overpass API query
- Download (using the Overpass API) the OSM features that will be mapped in that bounding box (buildings and/or amenities) as well as the OSM line features that will be used as cutlines to subdivide the area
- Trim the features within the bounding box but outside the AOI polygon
- Convert the polygon features into centroid points (needed because ODK select from map doesn't yet deal with polygons; this is likely to change in the future but for now we'll work with points only)
- Use line features as cutlines to create individual tasks (squares don't make sense for field mapping, neighborhoods delineated by large roads, watercourses, and railways do)
- Split the AOI into those tasks based on parameters set in the Manager Web Interface (number of features or area per task, splitting strategy, etc).
- Use the ODK Central API to create, on the associated ODK Central server:
  - A project for the whole AOI
  - One survey form for each split task (neighborhood)
    - This might require modifying the xlsforms (to update the version ID of the forms and change the name of the geography file being referred to). This is pretty straightforward using [OpenPyXL](https://openpyxl.readthedocs.io/en/stable/), though we have to be careful to keep the location within the spreadsheet of these two items consistent.
  - GeoJSON feature collections for each form (the buildings/amenities or whatever)
  - An App User for each form, which in turn corresponds to a single task. When the ODK Collect app on a user's phone is configured to function as that App User, they have access to _only_ the form and features/area of that task.
  - A set of QR Codes and/or configuration files/strings for ODK Collect, one for each App User

### Field Mapper Web Interface (with mobile-friendly map view)

- Ideally with a link that opens ODK Collect directly from the browser, but if that's hard, the fallback is downloading a QR code and importing it into ODK Collect.

## Frequently Asked Questions
### For Users
Q: What is FMTM?

A: FMTM stands for Field Monitoring Task Manager. It is a web-based application that facilitates remote monitoring of field activities for humanitarian organizations.

Q: Do I need to create an account to use the FMTM Web App?

A: No, you can use the FMTM Web App without creating an account, but creating an account allows you to contribute to mapping projects and access additional features.

Q: How do I browse and select mapping projects on the FMTM Web App?

A: You can browse and select mapping projects on the FMTM Web App by clicking on the "Projects" tab and selecting a project of interest. You can view project details, tasks, and mapping data on the project page.

Q: How do I contribute to a mapping project on the FMTM Web App?

A: To contribute to a mapping project on the FMTM Web App, you can create an account, select a project of interest, and choose a task to work on. You can then use the mapping tools provided to complete the task.

Q: Can I work on multiple mapping tasks at the same time on the FMTM Web App?

A: Yes, you can work on multiple mapping tasks at the same time on the FMTM Web App, as long as you can commit the necessary time and effort to each task.

Q: How do I know if my mapping work on the FMTM Web App is accurate?

A: The FMTM Web App has a validation process where other contributors review and validate the mapping work. This helps to ensure the accuracy of the mapping data.

Q: Can I provide feedback on a mapping project on the FMTM Web App?

A: Yes, you can provide feedback on a mapping project on the FMTM Web App by leaving a comment on the project page or contacting the project manager.

Q: How do I download mapping data from a project on the FMTM Web App?

A: To download mapping data from a project on the FMTM Web App, you can select the project of interest and click on the "Export" button on the project page.

Q: Can I use the mapping data from the FMTM Web App for my own research or projects?

A: The mapping data on the FMTM Web App is generally open and available for use, but it is important to check the specific project requirements and licenses before using the data for your own research or projects.

### For Contributors

Q: What is the Field Mapping Tasking Manager (FMTM)?

A: The Field Mapping Tasking Manager (FMTM) is an online platform that allows contributors to participate in mapping projects related to humanitarian and development work.

Q: How can I become a contributor to the FMTM?

A: To become a contributor to the FMTM, you can create an account on the platform and join a mapping project.

Q: Who can contribute to FMTM?

A: Anyone can contribute to FMTM. It is an open-source project, and contributions from developers, designers, and other contributors are always welcome.

Q: What kind of contributions can I make to FMTM?

A: There are several ways you can contribute to FMTM, including:

Development: If you have experience in web development, you can contribute by fixing bugs, adding new features, or improving the existing codebase.

Design: If you are a designer, you can contribute by improving the user interface, creating new design assets, or providing feedback on the existing design.

Documentation: If you have experience in technical writing, you can contribute by writing documentation, tutorials, or other educational materials.

Testing: If you have experience in software testing, you can contribute by testing the application and reporting bugs or suggesting improvements.

Translation: If you are fluent in a language other than English, you can contribute by translating the application or its documentation into your language.

Q: What technologies are used in FMTM?

A: FMTM is built using several technologies, including Django, Postgres, Redis, Celery, and Vue.js. The codebase is written in Python, HTML, CSS, and JavaScript.

Q: How do I set up FMTM locally?

A: To set up FMTM locally, you need to have Python, Postgres, Redis, and Node.js installed on your system. You can follow the instructions in the README file of the FMTM repository to set up the project.

Q: How can I report a bug or suggest a new feature for FMTM?

A: You can report bugs or suggest new features by opening an issue on the FMTM repository on GitHub. Be sure to provide as much detail as possible, including steps to reproduce the bug, screenshots, or mockups for new features.

Q: How can I contribute to FMTM if I'm new to open source or web development?

A: FMTM welcomes contributions from developers of all levels of experience, including those who are new to open source or web development. You can start by exploring the project's codebase and documentation, asking questions in the community, and contributing to issues labeled as "good first issue." Additionally, you can join the FMTM community on Slack to connect with other contributors and get help with your contributions.

Q: What are the benefits of contributing to the FMTM?

A: Contributing to the FMTM allows you to help with important humanitarian and development work, while also developing your mapping skills and knowledge.

Q: Do I need to have prior mapping experience to contribute to the FMTM?

A: No, prior mapping experience is not required to contribute to the FMTM. The platform provides training and resources to help new contributors get started.

Q: How do I know which mapping project to join?

A: The FMTM provides information about each project, including the location, the organization sponsoring the project, and the mapping goals. Review the project information and choose a project that interests you.

Q: Can I work on multiple mapping projects at the same time?

A: Yes, you can work on multiple mapping projects at the same time. However, it is important to ensure that you can commit the necessary time and effort to each project.

Q: How do I get feedback on my mapping work?

A: The FMTM provides a validation process where other contributors review and provide feedback on mapping work. You can also contact project managers or experienced contributors for additional feedback.

Q: How can I improve my mapping skills?

A: The FMTM provides training and resources to help you improve your mapping skills. You can also join mapping communities and forums to connect with other contributors and learn from their experiences.

Q: Can I use the mapping data for my own research or projects?

A: The mapping data on the FMTM is generally open and available for use, but it is important to check the specific project requirements and licenses before using the data for your own research or projects.

## Contributors ✨

Thanks goes to these wonderful people:

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<table>
  <tbody>
    <tr>
      <td align="center" valign="top" width="14.28%"><a href="http://ivangayton.net"><img src="https://avatars.githubusercontent.com/u/5991943?v=4?s=100" width="100px;" alt="Ivan Gayton"/><br /><sub><b>Ivan Gayton</b></sub></a><br /><a href="#projectManagement-ivangayton" title="Project Management">📆</a> <a href="https://github.com/hotosm/fmtm/commits?author=ivangayton" title="Code">💻</a> <a href="https://github.com/hotosm/fmtm/pulls?q=is%3Apr+reviewed-by%3Aivangayton" title="Reviewed Pull Requests">👀</a> <a href="#ideas-ivangayton" title="Ideas, Planning, & Feedback">🤔</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://www.hotosm.org"><img src="https://avatars.githubusercontent.com/u/71342768?v=4?s=100" width="100px;" alt="Rob Savoye"/><br /><sub><b>Rob Savoye</b></sub></a><br /><a href="#maintenance-robsavoye" title="Maintenance">🚧</a> <a href="#mentoring-robsavoye" title="Mentoring">🧑‍🏫</a> <a href="https://github.com/hotosm/fmtm/commits?author=robsavoye" title="Code">💻</a> <a href="https://github.com/hotosm/fmtm/pulls?q=is%3Apr+reviewed-by%3Arobsavoye" title="Reviewed Pull Requests">👀</a> <a href="#ideas-robsavoye" title="Ideas, Planning, & Feedback">🤔</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/krtonga"><img src="https://avatars.githubusercontent.com/u/7307817?v=4?s=100" width="100px;" alt="krtonga"/><br /><sub><b>krtonga</b></sub></a><br /><a href="https://github.com/hotosm/fmtm/commits?author=krtonga" title="Code">💻</a> <a href="https://github.com/hotosm/fmtm/commits?author=krtonga" title="Documentation">📖</a> <a href="#tool-krtonga" title="Tools">🔧</a> <a href="#ideas-krtonga" title="Ideas, Planning, & Feedback">🤔</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/spwoodcock"><img src="https://avatars.githubusercontent.com/u/78538841?v=4?s=100" width="100px;" alt="Sam"/><br /><sub><b>Sam</b></sub></a><br /><a href="https://github.com/hotosm/fmtm/commits?author=spwoodcock" title="Code">💻</a> <a href="https://github.com/hotosm/fmtm/pulls?q=is%3Apr+reviewed-by%3Aspwoodcock" title="Reviewed Pull Requests">👀</a> <a href="#infra-spwoodcock" title="Infrastructure (Hosting, Build-Tools, etc)">🚇</a> <a href="#ideas-spwoodcock" title="Ideas, Planning, & Feedback">🤔</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://www.hotosm.org/people/petya-kangalova/"><img src="https://avatars.githubusercontent.com/u/98902727?v=4?s=100" width="100px;" alt="Petya "/><br /><sub><b>Petya </b></sub></a><br /><a href="https://github.com/hotosm/fmtm/commits?author=petya-kangalova" title="Documentation">📖</a> <a href="#eventOrganizing-petya-kangalova" title="Event Organizing">📋</a> <a href="#ideas-petya-kangalova" title="Ideas, Planning, & Feedback">🤔</a></td>
      <td align="center" valign="top" width="14.28%"><a href="http://zanrevenue.org"><img src="https://avatars.githubusercontent.com/u/52991565?v=4?s=100" width="100px;" alt="Mohamed Bakari Mohamed"/><br /><sub><b>Mohamed Bakari Mohamed</b></sub></a><br /><a href="https://github.com/hotosm/fmtm/commits?author=Mudi-business" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://www.scdhub.org"><img src="https://avatars.githubusercontent.com/u/4379874?v=4?s=100" width="100px;" alt="G. Willson"/><br /><sub><b>G. Willson</b></sub></a><br /><a href="https://github.com/hotosm/fmtm/commits?author=biomassives" title="Code">💻</a></td>
    </tr>
    <tr>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/Ndacyayisenga-droid"><img src="https://avatars.githubusercontent.com/u/58124613?v=4?s=100" width="100px;" alt="Tayebwa Noah"/><br /><sub><b>Tayebwa Noah</b></sub></a><br /><a href="https://github.com/hotosm/fmtm/commits?author=Ndacyayisenga-droid" title="Documentation">📖</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/mohammadareeb95"><img src="https://avatars.githubusercontent.com/u/77102111?v=4?s=100" width="100px;" alt="Mohammad Areeb"/><br /><sub><b>Mohammad Areeb</b></sub></a><br /><a href="https://github.com/hotosm/fmtm/commits?author=mohammadareeb95" title="Documentation">📖</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/AugustHottie"><img src="https://avatars.githubusercontent.com/u/96122635?v=4?s=100" width="100px;" alt="AugustHottie"/><br /><sub><b>AugustHottie</b></sub></a><br /><a href="https://github.com/hotosm/fmtm/commits?author=AugustHottie" title="Documentation">📖</a></td>
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
