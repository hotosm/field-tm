# ❓ Frequently Asked Questions ❓

## General

### What is the Field Tasking Manager (Field-TM)?

The Field Tasking Manager (Field-TM) is an online platform that
allows contributors to participate in mapping projects related to
humanitarian and development work.

---

### What problem does it solve?

There are a few great tools for adding tags to OpenStreetMap in the field
already. Field-TM is not aiming to compete with these tools, but instead
has two goals:

1. To solve the challenge of effectively coordinating mappers to work together
   when mapping an entire area of interest. It can be difficult to **subdivide tasks**
   and know **who is working on what tasks.**. Field-TM should solve this problem.

2. Allow for coordinated field mapping **both inside and outside of OpenStreetMap**.
   Sometimes OpenStreetMap is not an appropriate target for the collected data,
   so a data flow outside of this ecosystem should be possible too.

---

### What makes Field-TM unique in this space?

- Fully open-source.
- Manages both **coordination** and **data collection\*** in one framework.
- Roadmapping input from the rich HOTOSM community.

  !!! note

        The data collection* portion is outsourced to the excellent
        ecosystem of ODK tools underneath.

---

### Don't other tools do similar things?

!!! note

      The following is the personal opinion from HOT staff members, and provides
      some context for the reasoning behind creating the Field-TM.

Generic field mapping:

- **QField**: the mobile extension of QGIS, literally a GIS on your phone.
  This is an excellent tool for what it does: collecting geometries in the
  field, alongside unstructured attributes like any other GIS.
  This is in contrast to tools such as ODK or Kobo that mostly
  collect structured survey data, by asking the user sets of predefined
  questions.

- **Fulcrum**: proprietary / paid. Appears to be more focused on data collection
  in engineering and environmental contexts, mostly for for-profit companies.
  We could possibly learn from them, but they are closed-source.

- **ArcGIS Field Maps**: proprietary / paid, similar applications to Fulcrum,
  but not necessarily designed for text/question based surveys.

Field survey-based data collection:

- **KoboCollect**: fork of ODK, same mobile app essentially, but different back end.
  Has a slightly complicated relationship with ODK, formerly taking from the
  community and not giving back. In our opinion, ODK is more innovative in pushing
  field data collection forward. Kobo do provide a free public server backed by the
  UN, as a general public good, and is widely adopted as a result.

- **Ona**: ODK-compatible software that also has a difficult relationship with Kobo.
  The history is complex, but at some point Ona had to make their front end
  closed-source. They have a lot of open-source components (like their back end)
  and have done some great work around data management and analytics, however,
  their main objective is not the same as Field-TM: _coordinating_ field mapping.

- **ODK**: I won't cover much here, as we talk about it a lot elsewhere.
  If you are collected mobile survey data then this is a tool at the forefront
  of that space. Many other tools replicate what ODK do.

- **ArcGIS Survey123**: proprietary / paid, more appropriate for our use case
  over ArcGIS Field Maps. However, not an option due to it's closed nature.

- **CommCare**: open-source, developed by Dimagi, and good for collecting survey
  data. It does not, however, use the open XForm / XLSForm standards like ODK,
  Kobo, and Ona. Very good at collection of "longitudinal data" (data over time),
  which ODK has only recently began to address with Entities.
  However there are two key missing features:
  (1) it's not well set up to handle geospatial data. It is possible to collect a
  GPS point of users in the field, but not possible to select geometries to map.
  (2) it's not configured to coordinate a team of users for field mapping, but more
  for individual users to map.
  Despite this we will definitely look for opportunities to learn from / collaborate
  into the future.

OpenStreetMap tagging:

- **StreetComplete**: a super simple and intuitive mobile app for improving
  OpenStreetMap. New features can be mapped, in addition to tags, directly
  uploaded to OSM. While Field-TM definitely wants to be used to update
  OSM, it's not the only usage mode we need to focus on (often users need
  less public data, such as slum mapping or census data). The app is also
  very much focused on editing as an _individual_, and not about coordinated
  mapping as a team.

- **EveryDoor**: another excellent app in the OSM ecosystem, perhaps focused
  slightly more at power users. It has many similar great features as
  StreetComplete, but also has the same properties that make it not a direct
  competitor for Field-TM.

In the long run, these two tools would be excellent candidates for integration
at the low level of Field-TM. It is conceivable that a field mapping campaign
could possibly use **either** ODK, StreetComplete, or EveryDoor to do the
actual mapping (while Field-TM coordinates).

Unmaintained projects:

- **MapCampaigner**: a now dead project. In our opinion, this tool certainly helped
  the Monitoring & Evaluation team for field data collection projects, but did not
  add anything innovative in terms of user experience for the the field mapper.

- **POSM** (+ OpenMapKit): a now dead project. However, this was an excellent technical
  advancement and concept for the open mapping sector. It was arguably the first
  good solution for field mobile data collection (using ODK and other tools
  underneath). OpenMapKit was the data collection system, while POSM was the offline
  server supporting it in the field. Unfortunately, the architecture around this
  was poorly designed, making it difficult to maintain into the future, meaning
  the project failed between 2014-2017.

  !!! note

        The gap left by this only started to be filled with the advent of the
        'Select From Map' functionality in ODK in 2018 (partly originally written
        by Ping @ ODK, with support from HOT and Ramani Huria @ OMDTZ).

        It is still useful to learn from the legacy of this tool around offline
        deployment on a small field-based device (e.g. RaspberryPI), and is
        currently in our roadmap to explore this approach further.

---

### So why should I use Field-TM over these other tools?

You might not need to! It depends if you are simply collecting data
in the field as an individual, or are trying to coordinate amongst
a team of enumerators.

Field-TM does not attempt to compete within the very rich field data
collection ecosystem. Instead, it is a higher level tool, aimed at
**coordination** of enumerators using one of these tools.

---

### What is the relationship between Field-TM and Kobo?

- Kobo is not an Field-TM competitor, it's an ODK competitor.
- Field-TM uses ODK underneath for reasons explained above, but due to the popularity
  of Kobo, could (and should) probably support the Kobo data collection app going
  forward.
- This does raise challenges, as new features integrated in ODK Collect take approx
  6 months to be integrated into KoboCollect.

  !!! note

        The adoption barrier for migrating from KoboCollect to ODK Collect should
        be minimal due to KoboCollect essentially being a re-branded version of
        ODK.

- Kobo does provide a free data collection server, supported by UN OCHA, meaning
  Kobo adoption in developing countries is currently a lot higher.

  !!! note

        HOT also aims to provide am equivalent free ODK data collection server:
        [https://odk.hotosm.org](https://odk.hotosm.org)

- The Kobo backend is currently (2024) a Python application based an old open-source
  tool called FormHub. The functionality of Kobo's and ODK's backends has diverged
  significantly over time. However, recently ODK have completely overhauled their
  backend to a Node server called ODK Central, which is rock-solid and much more
  advanced than the competition.
- The Kobo web-based form builder is still a big differentiator between the tools,
  as it is much more user-friendly (less technical) than ODK's requirement to know
  XLSForm language. However the capability of the web form builder is much less
  sophisticated than directly using XLSForms. It's nevertheless very useful for
  beginners.

## Info For Users

### Do I need to create an account to use the Field-TM Web App?

Mappers have no requirement to sign up, easing the process of mapping
for those that are impatient to get started! However, to use the Field-TM project
management site it is recommended to sign in with OSM. This is so data uploaded
to OSM can be attributed to a user. Notifications are also sent via OpenStreetMap
messages/emails.

---

### How do I contribute to a mapping project on the Field-TM Web App?

To contribute to a mapping project on the Field-TM Web App, you can
create an account, select a project of interest, and choose a task to
work on. You can then use the mapping tools provided to complete the
task.

---

### Can I work on multiple mapping tasks at the same time on the Field-TM Web App?

Yes, you can work on multiple mapping tasks at the same time on the
Field-TM Web App, as long as you can commit the necessary time and effort
to each task.

---

### How do I know if my mapping work on the Field-TM Web App is accurate?

The Field-TM Web App has a validation process where other contributors
review and validate the mapping work. This helps to ensure the
accuracy of the mapping data.

---

### Can I provide feedback on a mapping project on the Field-TM Web App?

Yes, you can provide feedback on a mapping project on the Field-TM Web
App by leaving a comment on the project page or contacting the project
manager.

---

### How do I download mapping data from a project on the Field-TM Web App?

To download mapping data from a project on the Field-TM Web App, you
can select the project of interest and click on the "Export" button on
the project page.

---

### Can I use the mapping data from the Field-TM Web App for my own research or projects?

The mapping data on the Field-TM Web App is generally open and
available for use, but it is important to check the specific project
requirements and licenses before using the data for your own research
or projects.

---

### What are the benefits of contributing to the Field-TM?

Contributing to the Field-TM allows you to help with important
humanitarian and development work, while also developing your mapping
skills and knowledge.

---

### Do I need to have prior mapping experience to contribute to the Field-TM?

No, prior mapping experience is not required to contribute to the
Field-TM. The platform provides training and resources to help new
contributors get started.

---

### Can I work on multiple mapping projects at the same time?

Yes, you can work on multiple mapping projects at the same
time. However, it is important to ensure that you can commit the
necessary time and effort to each project.

---

### How do I get feedback on my mapping work?

The Field-TM provides a validation process where other contributors
review and provide feedback on mapping work. You can also contact
project managers or experienced contributors for additional feedback.

---

## Info For Project Managers

### Can I use my own ODK Central instance?

Yes, you can. We understand in many cases users may already have
an instance of ODK Central (for example, at at organisational level),
so you may use your own server and credentials.

Please ensure the user credentials have 'Administrator' level permission,
else Field-TM project creation will not work.

The credentials should be provided when requesting the creation of an
'Organisation' in Field-TM.

Alternatively, you may request credentials for the HOT Global
[ODK Central Instance](https://odk.hotosm.org).

---

## Info For Repository Contributors

### How can I become a contributor to the Field-TM?

To become a contributor to the Field-TM, you can create an account on
Github and contribute to issues, discussions, or pull requests.

---

### Who can contribute to Field-TM?

Anyone can contribute to Field-TM. It is an open-source project, and
contributions from developers, designers, and other contributors are
always welcome.

---

### What kind of contributions can I make to Field-TM?

There are several ways you can contribute to Field-TM, including:

**Development**: If you have experience in web development, you can
contribute by fixing bugs, adding new features, or improving the
existing codebase.

**Design**: If you are a designer, you can contribute by improving the
user interface, creating new design assets, or providing feedback on
the existing design.

**Documentation**: If you have experience in technical writing, you can
contribute by writing documentation, tutorials, or other educational
materials.

**Testing**: If you have experience in software testing, you can
contribute by testing the application and reporting bugs or suggesting
improvements.

**Translation**: If you are fluent in a language other than English, you
can contribute by translating the application or its documentation
into your language.

---

### What technologies are used in Field-TM?

Field-TM is built using several technologies, including FastAPI,
Postgres, React, Svelte, and web components. The codebase is written in
Python & TypeScript mostly.

---

### How do I set up Field-TM locally?

To set up Field-TM locally, the simplest approach is likely using Docker.
If you are an advanced user, it is possible to run each service individually too.
Please follow the instructions in the setup guide on this site.

---

### Help! Cloning the repo doesn't work for me

If you are receiving errors cloning the repo, it may be an unstable internet
connection causing issues.

First, please check your internet connection, or use another connection if
possible.

One option to reduce the amount of content that needs to be downloaded
is to do a shallow clone:

    ```bash
    # Shallow clone only the `dev` branch
    git clone --depth 1 --no-single-branch https://github.com/hotosm/fmtm.git
    ```

To pull additional branches as you need them (for example, to work on them):

    ```bash
    git fetch origin branch-name
    git checkout branch-name
    ```

As an **absolute last resort**, you could try the following:

    ```bash
    # Set HTTP version to 1.1 for stability (multiple connections vs multiplexing)
    git config --global http.version HTTP/1.1

    # Increase timeout to 3 minutes
    git config --global http.lowSpeedTime 180

    # Allow retries in case of failure
    git config --global http.retry 3

    # Disable integrity checks for easier resume
    git config --global fetch.fsckObjects false
    git config --global fetch.writeCommitGraph false

    # Your clone command here...
    ```

---

### How can I report a bug or suggest a new feature for Field-TM?

You can report bugs or suggest new features by opening an issue on
the Field-TM repository on GitHub. Be sure to provide as much detail as
possible, including steps to reproduce the bug, screenshots, or
mockups for new features.

---

### How can I contribute to Field-TM if I'm new to open source or web development?

Field-TM welcomes contributions from developers of all levels of
experience, including those who are new to open source or web
development. You can start by exploring the project's codebase and
documentation, asking questions in the community, and contributing to
issues labeled as "good first issue." Additionally, you can join the
Field-TM community on Slack to connect with other contributors and get
help with your contributions.

---

## Advanced Use Cases

### How can I work with an offline basemap?

- Download MBTiles from Field-TM.
- Load MBTiles into ODK Collect via
  [this guide](https://docs.getodk.org/collect-offline-maps)

### Can I edit my XLSForm after I create a project?

- XLSForms can be updated!
- Go to the 'Manage Project' section.
- Edit --> Form Update.
- You can download the existing form from here.
- Edit the form, then upload and click the 'Update' button.
- This will update the form in ODK also.

### Can I record features that don't exist on the map yet?

Yes!

- Click on a task area.
- Then click to 'Add new feature'.
- This will open the Form to collect data.
- One of the form questions will ask you to record a geopoint of the
  feature location.

### Can I lock multiple tasks as once for mapping or validation?

Yes!

- There should be no issue doing this.
- However, note that if there is no activity on a locked task
  after a period of time, the task may auto-unlock, allowing
  other mappers to lock and contribute.

### What is the custom ODK Collect app?

- ODK Collect is an excellent mobile application.
- We need a slightly modified functionality of the app, so have created
  a custom version for you to use with Field-TM.
- We maintain a good relationship with the ODK developers and would like
  to get this functionality into the map app (meaning no custom app is required).
- However, this will take time!

### Why do I need the custom ODK Collect app?

- Ideally when we open ODK Collect, we want our feature / building to be
  selected already, avoiding the need to open the map and select it manually.
- We created the custom ODK Collect for exactly this purpose!
- It also opens the possibility of more advanced map capabilities in Field-TM,
  such as navigation to your chosen feature and directions.
- Hopefully it provides a more seamless user experience of Field-TM, that we
  can't provide with the default Collect.

### How do I install the custom ODK Collect app?

- First, open the sidebar on Field-TM and click the button to download the
  custom ODK Collect `.apk` file.
- If you don't have ODK Collect installed already, then you should be able to
  click this file and install as normal.
- If you already have ODK Collect installed, then you **may** have to uninstall
  this version first, prior to installing the custom version. This is to avoid
  version conflicts.
