# ❓ Frequently Asked Questions ❓

## General

**Q:** What is the Field Mapping Tasking Manager (FMTM)?

**A:** The Field Mapping Tasking Manager (FMTM) is an online platform that
allows contributors to participate in mapping projects related to
humanitarian and development work.

---

Q: What problem does it solve?

**A:** There are a few great tools for adding tags to OpenStreetMap in the field
already. FMTM is not aiming to compete with these tools, but instead has two goals:

    1. To solve the challenge of effectively coordinating mappers to work together
    when mapping an entire area of interest. It can be difficult to **subdivide tasks**
    and know **who is working on what tasks.**. FMTM should solve this problem.

    2. Allow for coordinated field mapping outside of OpenStreetMap. Sometimes
    OpenStreetMap is not an appropriate target for the collected data, so a data
    flow outside of this ecosystem should be possible too.

---

Q: Don't other tools do similar things?

**A:**

!!! note

    The following is the personal opinion from HOT staff members, and provides some
    context for the reasoning behind creating the FMTM.

- _Fulcrum_: proprietary / paid. Appears to be more focused on data collection in
  engineering and environmental contexts, mostly for for-profit companies.
  We could possibly learn from them, but they are closed-source.

- _ArcGIS Field Maps_: proprietary / paid, similar applications to Fulcrum, but not
  necessarily designed for text/question based surveys.

- _ArcGIS Survey123_: proprietary / paid, more appropriate for our use case of field
  survey data collection. However, not an option due to it's closed nature.

- _KoboCollect_: fork of ODK, same mobile app essentially, but different back end.
  Has a slightly complicated relationship with ODK, formerly taking from the
  community and not giving back. However, they now contribute financially to ODK,
  and definitely have some great ideas in this field. In our opinion, ODK is more
  innovative in pushing field data collection forward though. Kobo do provide a
  free public server backed by the UN, as a general public good, and is widely
  adopted as a result.

- _Ona_: proprietary software, with a slightly shady history of building open-source
  tools using NGO money, then changing the license to a closed model. Were legally
  forced to open-source the original work done, but everything since has been closed.
  Have since done some great work around data management and analytics, however,
  their main objective is not the same as FMTM: coordinating field mapping.

- _MapCampaigner_: a now dead project. In our opinion, this tool certainly helped
  the Monitoring & Evaluation team for field data collection projects, but did not
  add anything innovative in terms of user experience for the the field mapper.

- _POSM_ (+ OpenMapKit): a now dead project. However, this was an excellent technical
  advancement and concept for the open mapping sector. It was arguably the first
  good solution for field mobile data collection (using ODK and other tools
  underneath). OpenMapKit was the data collection system, while POSM was the offline
  server supporting it in the field. Unfortunately, the architecture around this
  was poorly designed, making it difficult to maintain into the future, meaning
  the project failed between 2014-2017.

!!! note

    The gap left by this only started to be filled with the advent of the
    'Select From Map' functionality in ODK in 2018 (partly originally written by
    Ping @ ODK, with support from HOT and Ramani Huria @ OMDTZ). It is still useful
    to learn from the legacy of this tool around offline deployment on a small
    field-based device (e.g. RaspberryPI), and is currently in our roadmap to explore
    this approach further.

- _CommCare_: technically open-source, developed by Dimagi, but built in such a way
  to make it quite difficult to self-host. Very good at collection of "longitudinal
  data" (data over time), which ODK has only recently began to address with Entities.
  We should definitely look for opportunities to learn from / collaborate into the
  future.

## For Users

**Q:** Do I need to create an account to use the FMTM Web App?

**A:** Mappers have no requirement to sign up, easing the process of mapping
for those that are impatient to get started! However, to use the FMTM project
management site it is recommended to sign in with OSM. This is so data uploaded
to OSM can be attributed to a user. Notifications are also sent via OpenStreetMap
messages/emails.

---

**Q:** How do I contribute to a mapping project on the FMTM Web App?

**A:** To contribute to a mapping project on the FMTM Web App, you can
create an account, select a project of interest, and choose a task to
work on. You can then use the mapping tools provided to complete the
task.

---

**Q:** Can I work on multiple mapping tasks at the same time on the FMTM Web App?

**A:** Yes, you can work on multiple mapping tasks at the same time on the
FMTM Web App, as long as you can commit the necessary time and effort
to each task.

---

**Q:** How do I know if my mapping work on the FMTM Web App is accurate?

**A:** The FMTM Web App has a validation process where other contributors
review and validate the mapping work. This helps to ensure the
accuracy of the mapping data.

---

**Q:** Can I provide feedback on a mapping project on the FMTM Web App?

**A:** Yes, you can provide feedback on a mapping project on the FMTM Web
App by leaving a comment on the project page or contacting the project
manager.

---

**Q:** How do I download mapping data from a project on the FMTM Web App?

**A:** To download mapping data from a project on the FMTM Web App, you
can select the project of interest and click on the "Export" button on
the project page.

---

**Q:** Can I use the mapping data from the FMTM Web App for my own research or projects?

**A:** The mapping data on the FMTM Web App is generally open and
available for use, but it is important to check the specific project
requirements and licenses before using the data for your own research
or projects.

---

## For Contributors

**Q:** How can I become a contributor to the FMTM?

**A:** To become a contributor to the FMTM, you can create an account on
the platform and join a mapping project.

---

**Q:** Who can contribute to FMTM?

**A:** Anyone can contribute to FMTM. It is an open-source project, and
contributions from developers, designers, and other contributors are
always welcome.

---

**Q:** What kind of contributions can I make to FMTM?

**A:** There are several ways you can contribute to FMTM, including:

Development: If you have experience in web development, you can
contribute by fixing bugs, adding new features, or improving the
existing codebase.

Design: If you are a designer, you can contribute by improving the
user interface, creating new design assets, or providing feedback on
the existing design.

Documentation: If you have experience in technical writing, you can
contribute by writing documentation, tutorials, or other educational
materials.

Testing: If you have experience in software testing, you can
contribute by testing the application and reporting bugs or suggesting
improvements.

Translation: If you are fluent in a language other than English, you
can contribute by translating the application or its documentation
into your language.

---

**Q:** What technologies are used in FMTM?

**A:** FMTM is built using several technologies, including FastAPI,
Postgres, React, and web components. The codebase is written in
Python & TypeScript mostly.

---

**Q:** How do I set up FMTM locally?

**A:** To set up FMTM locally, the simplest approach is likely using Docker.
If you are an advanced user, it is possible to run each service individually too.
Please follow the instructions in the setup guide on this site.

---

**Q:** How can I report a bug or suggest a new feature for FMTM?

**A:** You can report bugs or suggest new features by opening an issue on
the FMTM repository on GitHub. Be sure to provide as much detail as
possible, including steps to reproduce the bug, screenshots, or
mockups for new features.

---

**Q:** How can I contribute to FMTM if I'm new to open source or web development?

**A:** FMTM welcomes contributions from developers of all levels of
experience, including those who are new to open source or web
development. You can start by exploring the project's codebase and
documentation, asking questions in the community, and contributing to
issues labeled as "good first issue." Additionally, you can join the
FMTM community on Slack to connect with other contributors and get
help with your contributions.

---

**Q:** What are the benefits of contributing to the FMTM?

**A:** Contributing to the FMTM allows you to help with important
humanitarian and development work, while also developing your mapping
skills and knowledge.

---

**Q:** Do I need to have prior mapping experience to contribute to the FMTM?

**A:** No, prior mapping experience is not required to contribute to the
FMTM. The platform provides training and resources to help new
contributors get started.

---

**Q:** How do I know which mapping project to join?

**A:** The FMTM provides information about each project, including the
location, the organization sponsoring the project, and the mapping
goals. Review the project information and choose a project that
interests you.

---

**Q:** Can I work on multiple mapping projects at the same time?

**A:** Yes, you can work on multiple mapping projects at the same
time. However, it is important to ensure that you can commit the
necessary time and effort to each project.

---

**Q:** How do I get feedback on my mapping work?

**A:** The FMTM provides a validation process where other contributors
review and provide feedback on mapping work. You can also contact
project managers or experienced contributors for additional feedback.

---

**Q:** How can I improve my mapping skills?

**A:** The FMTM provides training and resources to help you improve your
mapping skills. You can also join mapping communities and forums to
connect with other contributors and learn from their experiences.
