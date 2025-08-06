# Road Survey

## project creation

- Admin who has permission to create project should create a project
  by filling all necessary data.
- Fill basic information like project name and descriptions.
- Select organisation and project managers.
- Draw or Upload project boundary and create draft project.

  ! Tips:
  We accept both polygon and multipolygon for project boundary. But the
  multipolygon is merged and accepted as single polygon moving forward. So
  if you have disjoint polygons, we suggest to create multiple projects

<img width="800" height="500" alt="FireShot Capture 1470 - 
project creation test - HOT Field Tasking Manager -  dev fmtm hotosm org"
 src="https://github.com/user-attachments/assets/
 ba189993-9283-48c2-8495-80164e5c1d2b" />

- You may choose the project type, add necessary hashtags, choose on
 whether to use default webform or odk collect mobile app for mapping
  exercises.
- You can enable and add TMS URL of base imagery if you have clearer
  satellite imagery of your project area.

<img width="800" height="500" alt="image" 
src="https://github.com/user-attachments/assets/
e73bf417-70fa-49b2-9974-ca876cdbf1e1" />

- Select OSM Highway as survey category under
  "what are you surveying category".
- When selected, download form option is enabled. Click to
  download highway xls form.
- Modify the form as your project need or upload the file as it is.
- When uploaded, make sure to confirm the form is valid.

<img width="800" height="500" alt="image" 
src="https://github.com/user-attachments/assets/
09eda08d-45a8-42cb-b724-bdefe7844822" />

- In forth step, Choose line as geometry to map.
- If you wish to include other related features like
  bridges as new feature, You can enable "I want to use a mix of
  geometry type" and select which type of new
  geometry feature you will map in field.
- If you are drawing lines for new feature encountered in field 
  then you can disable the option and move ahead.
- Select "Fetch data from OSM", if you want to download highway 
  within the project area from OSM.
- If you already have Highway data as geojson file, you can select
  "Fetch data from OSM"
  and upload the file. Refer 
  [HERE](https://docs.fmtm.dev/manuals/project-managers/#project-creation-tips)
  for project creation Tips
- If you are collecting features directly on field, then you can choose
  "No existing feature" and move ahead.

<img width="800" height="500" alt="image" 
src="https://github.com/user-attachments/assets/
a183eb30-c629-4f61-b82c-74b9634bde95" />

- For linear features survey, we suggest to use "Use uploaded AOI
  as task areas" rather thancreating multiple tasks. Hence
  other options of dividing area into square tasks and
  tasks splitting algorithms are disabled in this case.

  <img width="800" height="500" alt="image" src="https://github.com/
  user-attachments/assets/d31282f0-c3e6-47ef-958b-db8473e62c89" />
