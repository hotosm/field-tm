# 📖 History

## How was Field-TM born?

It started as Ivan's idea to build Field-TM (Ivan Gayton is Senior Humanitarian
Advisor at Humanitarian OpenStreetMap Team) which then became a collaborative
project with the efforts of Ivan, Rob Savoye who is Senior Technical Lead at
Humanitarian OpenStreetMap Team and many other members from HOT as well as
volunteers interested in the project.

HOT uses ODK heavily, but most of the data never makes it into OSM because all
the data processing is manual and slow, so it doesn't get done.

Ivan Gayton (Senior Humanitarian Advisor at Humanitarian OpenStreetMap Team)
heard about what Rob was working on and goes "That's the missing piece I
needed!". He'd been wanting to build Field-TM for years, but lacked the ability to
process the data.

A [webinar][1] then took place in September 2022
that showcased the high interest from the community and the need for
collaborative field mapping that really kicked off the starting point for
building the Field Tasking Manager.

**Want to know about OSM-Fieldwork project?** click [here][2]

## A project to provide tools for Open Mapping campaigns

The Field Tasking Manager (Field-TM) is a project that aims to provide tools
for coordinating field mapping activities in Open Mapping campaigns. While
there are existing field mapping applications, there is a lack of efficient
tools to coordinate these activities. The Field-TM builds on the HOT Tasking
Manager and other mapping applications to provide a more streamlined and
organized process for completing mapping tasks.

Currently, it is possible to implement a Field Tasking Manager workflow
using existing tools, but it requires significant effort and can be challenging.

The Field-TM project is developing automation features to address these challenges
and make the process more accessible to users.

By providing a centralized platform for organizing and managing mapping tasks,
assigning them to specific users, and tracking their progress, Field-TM aims to
simplify the coordination of mapping activities. The tool also provides
analytics and reporting features, allowing users to gain insights into mapping
campaigns and adjust their strategies accordingly.

Background and description of the project and idea are
[here][3]: please have a look at this blog if you haven't yet!

## How to contribute

The Field-TM project is open source and community-driven, welcoming contributions
from designers, user testers, and both front-end and back-end developers. If
you're interested in getting involved, please see our
[contributor guidelines][4]
for more information. We welcome questions and feedback, so don't hesitate
to reach out to us. 👍🎉

## Using ODK's Select From Map feature

ODK's Select From Map feature is a useful tool for field mappers to
collect data in a well-structured questionnaire format. The tool was
incorporated into ODK in mid-2022 and allows mappers to select an object from a
map, view its existing attributes, and fill out a form with new information
and attributes.

To prepare map files for ODK, inspiration is taken from the HOT Tasking Manager,
which allows remote mappers to choose well-defined small "task" areas, ensuring
full coverage of the project area and no unintended duplication of tasks. For
example, a mapper can approach a building, select that building from a map
view within ODK on their mobile phone, and add the opening hours, number of
floors, construction material, or any number of useful attributes in a
well-structured questionnaire format

To prepare the appropriate map files for ODK, we are taking our inspiration from
the [HOT Tasking Manager][5], which allows remote
mappers to choose well-defined small "task" areas, ensuring full coverage
of the project area and no unintended duplication of tasks.

## Users

There are three main user roles for using ODK's Select From Map feature:
campaign managers, field mappers, and validators.

### Campaign managers

Campaign managers select an Area of Interest (AOI) and organize field mappers
to go out and collect data. They need to:

<img
  align="right"
  width="400px"
  src="https://github.com/hotosm/fmtm/assets/97789856/9343a4bc-462c-44af-af93-8a67907837b3"
  alt="campaign-managers"
/>

- Select an AOI polygon by creating a GeoJSON or by tracing a polygon
  in a Web map
- Choose a task division scheme (number of features or area per task,
  and possible variations on what features to use as the preferred splitting lines)
- Provide specific instructions and guidance for field mappers on the project.
- Provide a URL to a mobile-friendly Web page where field mappers can, from
  their mobile phone, select a task that is not already "checked out"
  (or possibly simply allocate areas to the field mappers).
- See the status of tasks (open, "checked out", completed but not validated,
  requires to rework, validated, etc) in the Web browser on their computer

### Field mappers

Field mappers select (or are allocated) individual tasks within a project AOI
and use the ODK mobile app to gather data in those areas. They need to:

- Visit a mobile-friendly Web page where they can see available tasks on a map
- Choose an area and launch ODK Collect with the form corresponding to their
  allocated area pre-loaded

### Validators

Validators review the data collected by field mappers and assess its quality.
If the data is good, the validators merge the portion of the data that
belongs in OpenStreetMap to OSM. If it requires more work, the validators
either fix it themselves (for minor stuff like spelling or capitalization
mistakes that don't seem to be systematic) or inform the field mappers
that they need to fix it. They need to:

- Access completed data sets of "submissions" as Comma Separated Values
  and/or OSM XML so that they can review them.
- Mark areas as validated or requiring rework
- Communicate with field mappers if rework is necessary
- Merge good-quality data into OSM (probably from JOSM).
- Mark areas as completed and merged.

## Info for developers

For this visit the [Getting Started Page][6]

[1]: https://www.youtube.com/watch?v=GiLKRZpbtrc&\ab_channel=HumanitarianOpenStreetMapTeam
[2]: https://hotosm.github.io/osm-fieldwork/
[3]: https://www.hotosm.org/updates/field-mapping-is-the-future-a-tasking-manager-workflow-using-odk
[4]: https://docs.fmtm.dev/CONTRIBUTING/
[5]: https://tasks.hotosm.org/
[6]: https://docs.fmtm.dev/dev/Setup/
