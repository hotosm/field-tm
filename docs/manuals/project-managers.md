# Project Manager Manual for Field-TM

This manual is a step by step guide for the project managers on how to get
started with the Field Tasking Manager.

## Introduction

A **Mapping Campaign** refers to an organized effort of collecting data
from a particular geographic area/feature and creating maps. This may
involve using various mapping technologies such as; GPS, satellite
imagery, or crowdsourced data. These technologies are used to gather
information about the area of interest.

Mapping campaigns can be carried out for lots of different purposes,
some examples are:

- Disaster Response and Recovery
- Environmental Conservation
- Urban planning or;
- Social and Political Activism.

They often involve collaboration between organizations like; Government
Agencies, Non-profit Groups and volunteers.

Once the data is collected, it is analyzed and processed to create
detailed maps that can have a variety of use cases. These could be:

- Identifying areas of need.
- Planning infrastructure and development projects.
- Understanding the impact of environmental changes on the landscape,
  etc.

## An Overview Of Field-TM In Relation To HOT, OSM and ODK

The **Humanitarian OpenStreetMap Team (HOT**) is a non-profit
organization that uses open mapping data to support humanitarian and
disaster response efforts around the world. **The Field Mapping Task
Manager (Field-TM)** is one of the tools that **HOT** used to coordinate and
manage mapping projects.

**Field-TM** is a software tool that helps project managers to organize and
manage mapping tasks. It assigns those tasks to volunteers and tracks
their progress. The tool includes features for collaborative editing,
data validation, and error detection. This ensures that the data
collected by volunteers is accurate and reliable.

**Field-TM** is designed to be used in conjunction with **Open Data Kit
(ODK)**. **ODK** is a free and open-source set of tools that allows
users to create, collect, and manage data with mobile devices. The
**ODK** provides a set of open-source tools that allow users to build
forms, collect data in the field, and aggregate data on a central
server. It is commonly used for data collection in research, monitoring
and evaluation, and other development projects.

Project managers use **Field-TM** to manage tasks and assign them to
volunteers. The data collected by the volunteer via ODK is typically
uploaded to **OpenStreetMap (OSM)** where it is used to create more
detailed and accurate maps of the affected area. **OSM** is a free and
open-source map of the world that is created and maintained by
volunteers.

Overall, the **Field-TM** tool is an important component of **HOT**'s
efforts to support disaster response and humanitarian efforts around the
world. By coordinating mapping activities and ensuring the accuracy and
reliability of the data collected by volunteers, **Field-TM** helps to
provide critical information that can be used to support decision-making
and improve the effectiveness of humanitarian efforts.

## Prerequisites

- Stable Internet connection.
- Basic bnowledge of field mapping. If you are new to mapping we suggest you
  read [this][1].

## Steps to Join An Organization

You may request to join an existing organization.

Alternatively, request the creation of a new organization for your team:

!!! note

        If you are already an organization manager, the button to do this will be
        hidden. Please contact the administrator to create a second organization.

1. Go to the Manage organization tab. You can see the number of organizations.
   On the top, there is a New button, clicking on which you can request
   for a new organization.

2. You have to provide your consent and fill up the form by providing
   necessary details like Organization name, URL, Description of
   organization, type of organization etc.
   ![image](https://github.com/user-attachments/assets/e808a57a-2cce-48e3-9e68-a7af3dfeb36d)

3. Now submit the form. The request will reach the Admin who will approve your
   organization and inform you through the email.
   ![image](https://github.com/user-attachments/assets/6efffe4c-f887-4ef0-95e5-b432ee227a91)

For small organisations, the organisation manager may also be the main project
manager.

All project manager permissions are granted to the organisation manager.

## Steps To Create A Project In Field-TM

Project creation access is provided to users who have organisation admin or
higher level of permission.

Go to [field-tm](https://field.hotosm.org/) and click **New Project**.

### Choose Your Project Type

Field-TM offers two project creation paths:

|                    | **Quick Setup — OSM Buildings**    | **Custom Project**                     |
| ------------------ | ---------------------------------- | -------------------------------------- |
| **Best for**       | Tagging existing buildings in OSM  | Everything else                        |
| **Field app**      | QField (Android & iOS)             | QField **or** ODK Collect              |
| **Survey form**    | Pre-built building survey          | Upload your own XLSForm                |
| **Map data**       | Auto-fetched from OpenStreetMap    | Upload, fetch from OSM, or start empty |
| **Task splitting** | Automatic (~10 buildings per task) | Configurable                           |
| **Setup time**     | ~1 minute                          | ~5 minutes                             |

---

## Quick Setup: Map OSM Buildings with QField

This is the fastest way to start a building-tagging campaign.
Everything is configured automatically — just draw your area.

**Field mapping happens in QField on Android or iOS.**

### Step 1 — Draw your area

1. Log in to Field-TM.
2. Click **New Project** and select **"Add tags to OSM buildings"**.
3. On the map, draw a freehand polygon around the area you want to map,
   or upload a GeoJSON file.
4. Click **Create Project**.

Field-TM will then automatically:

- Download building outlines from OpenStreetMap for your area.
- Split the area into tasks of roughly 10 buildings each, using roads,
  rivers, railways, and airstrips as natural task boundaries.
- Package a basemap for offline use (where available).
- Create a QField Cloud project with the pre-built building survey.

Project creation runs in the background. You will be redirected to a
status page and then to the project once it is ready.

!!! tip

    If no OSM buildings exist in the area yet, the project will still be
    created — mappers can digitise new buildings directly in QField.

### Step 2 — Share with mappers (QField)

Once the project is ready:

1. Go to the project page and copy the **QField project link** or
   display the **QR code**.
2. Mappers install **QField** on their Android or iOS device and log in
   with their QField Cloud account (free to create at
   [app.qfield.cloud](https://app.qfield.cloud)).
3. They scan the QR code or open the shared link to download the project.
4. Mapped data syncs to QField Cloud automatically or manually — the
   project manager can review progress from the Field-TM dashboard.

---

## Custom Project Setup (Advanced)

Use this path for anything other than tagging OSM buildings: roads,
water points, vaccination campaigns, census mapping, infrastructure
inspections, or any project where you need to bring your own form or
map data.

Mapping can use **QField (Android & iOS)** or **ODK Collect (Android)**.

### Step 1 — Create project details

1. Log in to Field-TM.
2. Click **New Project** and select **"Something else"**.
3. Fill in the project basics: name, description, and hashtag.
4. If you have drone imagery or other high-resolution basemap, add the
   TMS URL here.
5. Choose **Public** or **Private** visibility.
6. Choose the field mapping app:
   - **QField** — works on Android and iOS; supports offline basemaps
     and syncs via QField Cloud.
   - **ODK Collect** — Android only; submits directly to ODK Central.
7. Click **Next**.

![image](https://github.com/user-attachments/assets/c65c4ae2-d9be-4e45-ac71-a8b5653baba3)

### Step 2 — Define the project area

- Draw a freehand polygon on the map, or click **Upload file** to
  upload a GeoJSON AOI.
- Review the highlighted area on the map and click **Next**.

!!! tip

    Confirm the exact area before proceeding — the project boundary
    cannot be edited after the project is created.

![image](https://github.com/user-attachments/assets/64aeda34-c682-4fdc-8c2f-1fd83e29c61f)

### Step 3 — Upload the survey form

- Upload a pre-configured XLSForm, or browse the
  [community XLSForm gallery](https://xlsforms.field.hotosm.org) to
  download an existing one.
- Click **Next** once a form is selected.

See [XLS Form Preparation](#xls-form-preparation) for guidance on
preparing your form.

![image](https://github.com/user-attachments/assets/cdf1e050-42ec-4149-bf97-0d841bc5117f)

### Step 4 — Select map data

Choose what existing features (if any) mappers will survey:

- **Fetch from OSM** — downloads buildings or healthcare features for
  the AOI automatically.
- **Upload custom map data** — upload your own GeoJSON file of features.
- **No existing data** — mappers collect and digitise entirely new
  features in the field.

You can also upload a secondary supporting layer (e.g. administrative
boundaries) that mappers can see but cannot edit.

![image](https://github.com/user-attachments/assets/8df7c0fc-9a14-4d2d-bfdf-9fb8d9e92b89)

### Step 5 — Configure task splitting

Choose how the AOI is divided into mapper tasks:

- **Split into squares** — uniform grid; good for areas with sparse
  features.
- **Use uploaded areas** — use the uploaded AOI boundaries directly as
  task areas (one or many).
- **Split by feature count** — algorithm splits based on a target number
  of features per task; uses road/river lines as natural boundaries where
  possible.

Task splitting may take a few seconds to a few minutes depending on
feature count and AOI size. Click **Submit** to create the project.

![image](https://github.com/user-attachments/assets/7eeaf7ed-c13d-4444-aeeb-d71aed4fee8e)

### After creation — QField projects

If you selected **QField** as the field app:

1. Go to the project page and copy the **QField project link** or
   display the **QR code**.
2. Mappers log in to QField with a QField Cloud account
   ([app.qfield.cloud](https://app.qfield.cloud)) and scan the QR code
   or open the shared link to download the project.
3. Submissions sync back to QField Cloud; you can review them from the
   Field-TM submissions page.

### After creation — ODK Collect projects

If you selected **ODK Collect** as the field app:

1. Mappers install ODK Collect on Android.
2. Share the project URL (`https://field.hotosm.org/project/{project_id}`)
   or QR code so mappers can configure the app automatically.
3. Submissions go to ODK Central and appear in the Field-TM dashboard.

### Project Creation Tips

#### Preparing Map Features

- Ensure you have the map features ready for the area you plan to
  survey before starting project creation.
- The files should be in GeoJSON format, use the WGS coordinate
  system with EPSG 4326, and must not include a Z-coordinate.
  The map feature file should follow the osm tags structure.
- Below is a sample of the required file structure:

  !!! example

         ```json
         {
            "type": "Feature",
            "properties": { "full_id": "r9517874",
               "osm_id": "9517874",
               "osm_type": "relation"
               "tags": {"building": "yes"},
               "type": "multipolygon",
               "name": "",
               "building:levels": "" },
            "geometry": { "type": "MultiPolygon", "coordinates": [ [ [
               [ -3.9618848, 5.3041323 ],
               [ -3.9615121, 5.3041457 ],
               [ -3.9615028, 5.3038906 ],
               [ -3.9618755, 5.3038772 ],
               [ -3.9618848, 5.3041323 ]
            ],
            [
               [ -3.9620167, 5.3042236 ],
               [ -3.9620143, 5.3041258 ],
               [ -3.9619839, 5.3041266 ],
               [ -3.9619757, 5.3037882 ],
               [ -3.9614038, 5.3038019 ],
               [ -3.9614144, 5.3042381 ],
               [ -3.9620167, 5.3042236 ]
            ] ] ] }
         }
         ```

- You may download features from OpenStreetMap (OSM) by clicking on
  Fetch data from osm with Field-TM project creation; however, note that
  Field-TM is not responsible for the data quality of features extracted
  from OSM.
- Currently, available types of survey features are Buildings and
  Healthcare only. We plan to add more types of features moving ahead.
- Project managers can also upload supporting map features. Note that
  these secondary features can’t be surveyed but selected for respective
  primary features.

#### XLS Form Preparation

- Be prepared with the XLS form for the project.
- If updates are required to the form, you can edit the XLS form even
  after the project is created.
- Note that a few fields in the beginning and end of the form will be
  injected to ask for some feature verification.
- So project managers are requested to fill up the form through odk
  or download the form after the project is created to know about the
  field injected. You can also get the fields injected from our documentation
  [here][2]
- Also read carefully the overview in the left section of each step to
  understand the details of the functionalities.

#### Uploading Custom Imagery

- If you have custom imagery that you want to use as basemap during field
  mapping activity, then you have to add the TMS link of that imagery
  during the first step of project creation.

- Click on _I would like to include my own imagery layer for reference_
  in the first step to add TMS URL. You can get URL by uploading it in
  openaerialmap.

#### ODK Central Credentials

- To store your submissions in ODK Central, you need to have valid
  ODK Central credentials.
- One option is to use your own organisations ODK server, if available.
- Another is to request access to use HOT's ODK server, which is free
  to use for public project creation.

## Steps To View Your Submissions and Infographics

1. Go to the respective project. On the bottom left side,
   you will see the view infographics button.
2. Click on the button will lead you to the infographics page.
   ![image](https://github.com/user-attachments/assets/6d48dd40-1be6-4063-9d1c-0276633c6d7a)

3. On the right side there is an icon which will switch the layout to
   table view, meaning you can see the submissions in table format.
4. You can see the details of submission and also review the submission
   and set the submission as accepted, rejected or has issues. Moreover,
   you can also comment to the submission for mappers.
   ![image](https://github.com/user-attachments/assets/9a53611b-8c03-4aa8-84f9-299d538f696a)

5. Users can also download the submission in Json or CSV format.
6. The submission can also be uploaded to JOSM. For that, you should
   have JOSM software installed in your device and should have your remote
   control enabled.
   ![image](https://github.com/user-attachments/assets/b17df10f-df86-4ca1-abc4-97a34be1d6c3)

### Mapper Training

#### During Training

1. Share the link of the project for the mapper to reach
   to the project easily. The URL will be:
   `https://field.hotosm.org/project/{project_id}`
2. **Updating Metadata**  
   If you need mappers to include their email  
   and phone number along with their username, guide them  
   to update their ODK Collect settings:
   - Navigate to **Settings** for the project.
   - Click on **User and Device Identity** to update the  
     metadata fields.
3. **Test Submissions**  
   Encourage mappers to submit a few test entries to  
   familiarize themselves with the workflow and address  
   any issues during training.

#### After Training

1. Collect regular ongoing feedback from mappers to ensure they face no difficulties
   during fieldwork.
2. Prepare clear and detailed instructions for mappers
   and validators, specific to the project requirements.
3. Prepare the checklist for validation. The things to
   check may depend on the type of project.
4. Connect the odk central to powerBI or any other data visualisation tool via Odata
   link to customise the charts and graphs as per your need.  
   ![odk_image](image.png)

To get more info about project management in odk collect  
follow the guide [Here][5].

### Connecting The Data To External Applications

Field-TM submission data is accessible via **OData** — a standardised
feed format supported by many data analysis tools including Excel,
PowerBI, Tableau, Redash, and Grafana.

There are two OData endpoint types:

- **Submission data** — all form submissions:
  `/v1/projects/{projectId}/forms/{xmlFormId}.svc`
- **Entity data** — the features/entities dataset:
  `/v1/projects/{projectId}/datasets/{name}.svc`

For example:

- `https://odk.hotosm.org/v1/projects/86/forms/df9135c8-84b1-4753-b348-e8963a8b4088.svc`
- `https://odk.hotosm.org/v1/projects/86/datasets/features.svc`

You can find the exact URLs for your project inside ODK Central under
**Project → Form → OData Access**.

Authentication uses **Basic Auth** with your ODK Central username and
password.

#### Visualising in Microsoft Excel

Excel supports OData feeds natively via Power Query, making it a quick
option for exploratory analysis and simple dashboards without installing
additional software.

1. Open Excel and go to the **Data** tab.
2. Click **Get Data → From Other Sources → From OData Feed**.
3. Paste your OData URL (submission or entity endpoint) and click **OK**.
4. When prompted for authentication, select **Basic** and enter your
   ODK Central username and password.
5. The Power Query Navigator opens. Select the **`Submissions`** table
   (or `value` for entity feeds) and click **Transform Data** to open
   the Power Query Editor, or **Load** to import directly.
6. In Power Query you can expand nested JSON columns, filter rows,
   rename fields, and reshape the data before loading.
7. Once loaded into the worksheet, use **Insert → PivotTable** or
   **Insert → Chart** to build visualisations from the data.

> **Tip:** Click **Data → Refresh All** at any time to pull the latest
> submissions into your spreadsheet without repeating the setup.

#### Visualising in PowerBI

PowerBI is free, cross-platform, and well-suited for richer interactive
dashboards. ODK also has dedicated documentation on this workflow:
<https://docs.getodk.org/tutorial-mapping-households/>

1. Open PowerBI Desktop and click **Get Data → OData feed**.
2. Paste your OData URL and click **OK**.
3. Select **Basic** authentication and enter your ODK Central username
   and password.
4. In the Navigator, select the **`Submissions`** (or **`value`**) table
   and click **Transform Data**.
5. Use the Power Query Editor to expand nested columns, filter, and
   clean the data, then click **Close & Apply**.
6. Build your report by dragging fields onto the canvas and adding
   charts, maps, slicers, and other visuals.
7. Click **Refresh** to pull in the latest submissions at any time.

## Manage project and users

### Steps to Edit Project Details

1. Users can also edit a few fields after project creation like basic
   details like name, description, instructions as well as XLS form.

2. Go to the respective project you want to edit. Click on the
   manage button to edit basic details and XLS form.

   ![image](https://github.com/user-attachments/assets/a3225885-c6cd-4fa9-9352-ccd4a8709eff)

### Invite Users

You can invite users (mappers and project managers to your project).
If the user already exists in Field-TM, they will be directly assigned role.

If they are not registered on Field-TM,, the email invitation will
be sent, following which users can get necessary permission to that project.
You can invite users either through osm username or gmail.

1. Choose the mode of invitation, either through osm or gmail.
2. Provide respective osm username or email address. You can invite
   multiple users at a time.
3. Assign the role to users and click on invite.
4. In case of gmail invitation, copy the link and share to that user
   through other media.

## Help and Support

If you encounter any issues or need assistance while using Field-TM, you can access
the following resources:

- Check the [FAQs][3] .
- Ask your doubts in the [Slack channel: #field-mapping-tasking-manager][4]

[1]: https://tasks.hotosm.org/learn/map "If you are new to mapping"
[2]: https://docs.field.hotosm.org/manuals/xlsform-design/#injected-fields-in-the-field-tm-xls-form "injected fields"
[3]: https://docs.field.hotosm.org/faq "FAQs"
[4]: https://hotosm.slack.com/archives/C04PCBFDEGN "Slack channel: #field-mapping-tasking-manager"
[5]: https://docs.getodk.org/collect-using "Using Collect"
