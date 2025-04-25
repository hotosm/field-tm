# Types Of User In Field-TM

## Organisation Managers

- Oversee all projects within an organisation.
- Typically responsible for creating projects and assigning project managers
  to them.
- For a small organisation, the organisation manager may also be the project
  manager.

## Project / Campaign Managers

Campaign managers select an Area of Interest (AOI) and organize
field mappers to go out and collect data. They need to:

- Select an AOI polygon by creating a GeoJSON or by tracing a polygon in a Web map
- Choose a task division scheme (number of features or area per task,
  and possibly variations on what features to use as the preferred splitting lines)
- Provide specific instructions and guidance for field mappers on the project.
- Provide a URL to a mobile-friendly Web page where field mappers can,
  from their mobile phone, select a task that is not already "checked out"
  (or possibly simply allocate areas to the field mappers).
- Here is the link for the web page <https://mapper.fmtm.hotosm.org/{project_Id}>
- See the status of tasks (open, "checked out", completed but not validated,
  requires rework, validated, etc) in the Web browser on their computer

## Field Mappers

Field mappers select (or are allocated) individual tasks within a project
AOI and use the ODK mobile app to gather data in those areas. They need to:

- Visit a mobile-friendly Web page where they can see available tasks on a map

- Click here to visit the web page <https://mapper.fmtm.hotosm.org/{project_Id}>
- Choose an area and launch ODK Collect
  with the form corresponding to their allocated area pre-loaded

## Validators

Validators review the data collected by field mappers and assess its quality.
If the data is good, the validators merge the portion of the data that belongs
in OpenStreetMap to OSM.
If it requires more work, the validators either fix it themselves
(for minor stuff like spelling or capitalization mistakes that don't seem to be systematic)
or inform the field mappers that they need to fix it. They need to:

- Access completed data sets of "submissions" as Comma Separated Values
  and/or OSM XML so that they can review it.
- Mark areas as validated or requiring rework
- Communicate with field mappers if rework is necessary
- Merge good-quality data into OSM (probably from JOSM).
- Mark areas as completed and merged.
