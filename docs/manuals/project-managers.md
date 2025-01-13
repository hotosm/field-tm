# Project Manager Manual for FMTM

This manual is a step by step guide for the project managers on how to get
started with the Field Mapping Tasking Manager.

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

## An Overview Of FMTM In Relations With HOT, OSM and ODK

The **Humanitarian OpenStreetMap Team (HOT**) is a non-profit
organization that uses open mapping data to support humanitarian and
disaster response efforts around the world. **The Field Mapping Task
Manager (FMTM)** is one of the tools that **HOT** used to coordinate and
manage mapping projects.

**FMTM** is a software tool that helps project managers to organize and
manage mapping tasks. It assigns those tasks to volunteers and tracks
their progress. The tool includes features for collaborative editing,
data validation, and error detection. This ensures that the data
collected by volunteers is accurate and reliable.

**FMTM** is designed to be used in conjunction with **Open Data Kit
(ODK)**. **ODK** is a free and open-source set of tools that allows
users to create, collect, and manage data with mobile devices. The
**ODK** provides a set of open-source tools that allow users to build
forms, collect data in the field, and aggregate data on a central
server. It is commonly used for data collection in research, monitoring
and evaluation, and other development projects.

Project managers use **FMTM** to manage tasks and assign them to
volunteers. The data collected by the volunteer via ODK is typically
uploaded to **OpenStreetMap (OSM)** where it is used to create more
detailed and accurate maps of the affected area. **OSM** is a free and
open-source map of the world that is created and maintained by
volunteers.

Overall, the **FMTM** tool is an important component of **HOT**'s
efforts to support disaster response and humanitarian efforts around the
world. By coordinating mapping activities and ensuring the accuracy and
reliability of the data collected by volunteers, **FMTM** helps to
provide critical information that can be used to support decision-making
and improve the effectiveness of humanitarian efforts.

## Prerequisites

- Stable Internet connection.
- Basic bnowledge of field mapping. If you are new to mapping we suggest you
  read [this][1].

## Video Tutorial

<https://github.com/user-attachments/assets/963e7b22-5752-4158-b12d-e67c643235b8>

<https://github.com/user-attachments/assets/969e87e1-581c-4f76-93a7-0b4524b2db3a>

<https://github.com/user-attachments/assets/82b200bc-620a-4712-8d2e-3dcc4c553230>

<https://github.com/user-attachments/assets/03fe2d98-f441-4794-9a0d-5ae49722efed>

<https://github.com/user-attachments/assets/a54ee33c-359c-46f9-b9a4-e58c909569c8>

## Steps to Join An Organisation

You may request to join an existing organisation.

Alternatively, request the creation of a new organisation for your team:

1. Go to the Manage organization tab. You can see the number of organizations.
   On the top, there is a New button, clicking on which you can request
   for a new organization.

2. You have to provide your consent and fill up the form by providing
   necessary details like Organization name, URL, Description of
   organization, type of organization etc.
   ![image](https://github.com/user-attachments/assets/e808a57a-2cce-48e3-9e68-a7af3dfeb36d)

3. Now submit the form. The request will reach the Admin who will create your
   organization and inform you through the email.
   ![image](https://github.com/user-attachments/assets/6efffe4c-f887-4ef0-95e5-b432ee227a91)

## Steps To Create A Project In FMTM

1. Go to [fmtm][2] .
2. In the header, you'll find two tabs: Explore Projects and Manage Organization.

   ![image](https://github.com/user-attachments/assets/6bf8604b-d44c-4488-a8c6-5312fb75a975)

3. Start by exploring the projects listed by different nations and world
   communities for field mapping exercises.
4. Use the search option to narrow down the project cards or find the project
   of your choice.
5. If you are not logged into the system, the "Create new project" button will
   be disabled.
6. If you are new then on the top right corner click on Sign up and create an
   account . Else , Sign in to your existing account .
7. Once signed in, the "Create new project" button will be enabled. Click on it.
8. The process of creating a new project involves four steps: Project Details,
   Uploading the Area, Defining the Task, and Selecting the Form.
9. Start by filling in the project details, including the organization name,
   project name, description, and other relevant information.

   ![image](https://github.com/user-attachments/assets/c65c4ae2-d9be-4e45-ac71-a8b5653baba3)

10. If your organization's name is not listed, you can add it through the
    "Manage Organization" tab.
11. Provide the necessary credentials for the ODK (Open Data Kit) central setup,
    including URL, username, and password.
12. Proceed to the next step, which is uploading the area for field mapping.
    Choose the file option and select the AOI (Area of Interest) file in GEOJSON
    file format.
    Review the displayed map that corresponds to your selected area and click
    on "Next".

    ![image](https://github.com/user-attachments/assets/64aeda34-c682-4fdc-8c2f-1fd83e29c61f)

13. The step 3 is to choose the form category of the project. Meaning if you want
    to survey each household or healthcare or educational institutes.
    You can upload the custom XLS form by clicking on the checkbox.
    Click on "Next" to proceed.

    ![image](https://github.com/user-attachments/assets/cdf1e050-42ec-4149-bf97-0d841bc5117f)

14. In step 4, you can either generate the map features from osm or upload the
    custom map features.
    You can also upload additional map feature to have multiple feature
    selection supported.

    ![image](https://github.com/user-attachments/assets/8df7c0fc-9a14-4d2d-bfdf-9fb8d9e92b89)

15. The final step is task splitting which can be performed on three different
    ways. You can split the task on square of size you want. The second option
    is to choose area as task where you can use single polygon as a task. And
    the task splitting algorithm which splits the tasks with average number of
    features which is provided by project creator. The task splitting may take
    few seconds to few minutes considering the feature count and size of AOI.
    Click on "Submit" to create project.

    ![image](https://github.com/user-attachments/assets/7eeaf7ed-c13d-4444-aeeb-d71aed4fee8e)

16. Wait for the system to generate QR codes for each task, which will be used
    later in the field mapping process.
17. After the project creation is successful and QR codes are generated, you are
    redirected to the project details page of the project.

### Guidelines / Common Questions

#### Defining the Project Boundary

- Confirm the exact area for the survey before creating
  the project, as the project boundary cannot be
  edited once the project is created.

#### Preparing Map Features

- Ensure you have the map features ready for the area
  you plan to survey before starting project creation.
- The files should be in GeoJSON format, use the WGS coordinate
  system with EPSG 4326, and must not include
  a Z-coordinate. The map feature file should follow the
  osm tags structure.
- Below is a sample of the required file structure:

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
},
```

- You may download features from OpenStreetMap (OSM)
  by clicking on Fetch data from osm with FMTM project  
  creation; however, note that FMTM is not responsible  
  for the data quality of features extracted from OSM.
- Currently, available types of survey features are Buildings
  and Healthcare only. We plan to add more types of features moving ahead.
- Project managers can also upload supporting map features.
  Note that these secondary features can’t be surveyed but  
  selected for respective primary features.

#### XLS Form Preparation

- Be prepared with the XLS form for the project.
- If updates are required to the form, you can edit the  
  XLS form even after the project is created.
- Note that a few fields in the beginning and end of  
  the form will be injected to ask for some feature verification.
- So project managers are requested to fill up the  
  form through odk or download the form after the project  
  is created to know about the field injected. You can also  
  get the fields injected from our documentation  
  [Here](https://docs.fmtm.dev/manuals/xlsform-design/#injected-fields-in-the-fmtm-xls-form)

Also read carefully the overview in the left section of
each step to understand the details of the functionalities.

#### Uploading Custom Imagery

If you have custom imagery that you want to use as basemap
during field mapping activity, then you have to add the  
TMS link of that imagery during the first step of project creation.

- Click on _I would like to include my own imagery layer  
  for reference_ in the first step to add TMS URL. You can  
  get the URL by uploading it in openaerialmap.

#### ODK Central Credentials

To store your submissions in ODK Central, you need to  
have valid ODK Central credentials. You can obtain these  
by hosting your own ODK Central server. If you don’t have  
access to a personal ODK Central server, you can use HOT’s  
server by selecting HOT as your organization.

#### During Mapper Training

1. Make sure mapper has downloaded custom odk collect from  
   FMTM website. You can also share the apk file if mappers
   find it difficult to download by themselves.
2. Share the link of the project for the mapper to reach  
   to the project easily. The URL be:
   [https://fmtm.hotosm.org/mapnow/project_id](https://fmtm.hotosm.org/mapnow/project_id)
3. **Updating Metadata**  
   If you need mappers to include their email  
   and phone number along with their username, guide them  
   to update their ODK Collect settings:
   - Navigate to **Settings** for the project.
   - Click on **User and Device Identity** to update the  
     metadata fields.
4. **Test Submissions**  
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
follow the guide [Here](https://docs.getodk.org/collect-using/).

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

### Connecting The Data To External Applications

If you want to visualise the submissions and create custom charts
and diagrams using FMTM submissions, then you can follow the steps
below and load the submissions on any data analysis platform using **OData**.

OData endpoints are a standardised way to ingest
this data into other tools: PowerBI, Tableau, Redash, Grafana.

Why PowerBI? You can use other tools too like Tableau, Redash, Grafana or even
Excel. However, PowerBI is free to use, very powerful, and user friendly to use,
despite being a proprietary Microsoft tool.

The steps shows how to use PowerBI and create custom visualisations.
ODK already has good docs on this which you can refer to.
<https://docs.getodk.org/tutorial-mapping-households/>

Step 1: Start a new project, add a new data source 'OData Feed'

[Image here]

Step 2: Use the OData URLs shown in the ODK docs:
a. Submission data: /v1/projects/{projectId}/forms/{xmlFormId}.svc
e.g. <https://odk.hotosm.org/v1/projects/86/forms/df9135c8-84b1-4753-b348-e8963a8b4088.svc>
b. Entity data: /v1/projects/{projectId}/datasets/{name}.svc
e.g. <https://odk.hotosm.org/v1/projects/86/datasets/features.svc>

Step 3: Enter your credentials using Basic Auth

Step 4: Preview the data

Step 5: Transform data as needed, load into charts, graphs, etc, to create the
dashboard you need.

## Steps to Edit Project Details

1. Users can also edit a few fields after project creation like basic
   details like name, description, instructions as well as XLS form.

2. Go to the respective project you want to edit. Click on the
   manage button to edit basic details and XLS form.

   ![image](https://github.com/user-attachments/assets/a3225885-c6cd-4fa9-9352-ccd4a8709eff)

## Help and Support

If you encounter any issues or need assistance while using FMTM, you can access
the following resources:

- Check the [FAQs][3] .
- Ask your doubts in the [Slack channel: #field-mapping-tasking-manager][4]

[1]: https://tasks.hotosm.org/learn/map "If you are new to mapping"
[2]: https://fmtm.hotosm.org/ "fmtm"
[3]: https://docs.fmtm.dev/faq "FAQs"
[4]: https://hotosm.slack.com/archives/C04PCBFDEGN "Slack channel: #field-mapping-tasking-manager"
