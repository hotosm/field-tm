# User Manual for FMTM

This manual is a step by step guide for the project managers on how to get
started with the Field Mapping Tasking Manager.

- [User Manual for FMTM](#user-manual-for-fmtm)
  - [Introduction](#introduction)
  - [An Overview Of FMTM In Relations With HOT, OSM and ODK](#an-overview-of-fmtm-in-relations-with-hot-osm-and-odk)
  - [Prerequisites](#prerequisites)
  - [Video Tutorial](#video-tutorial)
  - [Steps to create a project in FMTM](#steps-to-create-a-project-in-fmtm)
  - [Steps to start access your project and Start mapping or a mapping campaign](#steps-to-start-access-your-project-and-start-mapping-or-a-mapping-campaign)
  - [Help and Support](#help-and-support)
  - [Thank you](#thank-you)

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

- Stable Internet connection
- Knowledge on field mapping . If you are new to mapping we suggest you to read
  [this][9] .
- Account on ODK Central Server.
  [Here][10]
  are the instructions for setting up an ODK Central server on Digital Ocean
  (it's very similar on AWS etc)

## Video Tutorial

<https://github.com/user-attachments/assets/963e7b22-5752-4158-b12d-e67c643235b8>

<https://github.com/user-attachments/assets/969e87e1-581c-4f76-93a7-0b4524b2db3a>

<https://github.com/user-attachments/assets/82b200bc-620a-4712-8d2e-3dcc4c553230>

<https://github.com/user-attachments/assets/03fe2d98-f441-4794-9a0d-5ae49722efed>

<https://github.com/user-attachments/assets/a54ee33c-359c-46f9-b9a4-e58c909569c8>

## Steps to create a project in FMTM

1. Go to [fmtm][11] .
2. In the header, you'll find two tabs: Explore Projects and Manage Organization.

   ![image](https://github.com/user-attachments/assets/6bf8604b-d44c-4488-a8c6-5312fb75a975)

3. Start by exploring the projects listed by different nations and world
   communities for field mapping exercises.
4. Use the search option to narrow down the project cards or find the project
   of your choice.
5. If you are not logged into the system, the "Create new project" button will
   be disabled.
6. If you are new then on the top right cornor click on Sign up and create an
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

## Steps to start access your project and Start mapping or a mapping campaign

1. Go to the Explore projects tab . Click on the project card and proceed to the
   next step.
2. Select one of the available tasks and start the field mapping exercise.

   ![image](https://github.com/user-attachments/assets/513a189d-04d9-4a30-9793-7cdfbb333069)

3. If a task is already locked by another user, choose a different task that is
   available for mapping.If a task is already locked by another user, choose a
   different task that is available for mapping.

   - The drop down icon beside **LEGEND** displays a color code. This
     color code lets you know the status of each task on the map.

     - **READY** means that task is available to be mapped
     - **LOCKED FOR MAPPING** means that task is already being mapped by another
       volunteer and therefore unavailable for mapping
     - **MAPPED** or **READY FOR VALIDATION** means that task has been completely
       mapped and ready to be validated.
     - **LOCKED FOR VALIDATION** means that task has been mapped and being
       validated.
     - **VALIDATED** means that task has successfully been validated and completely
       mapped with no errors
     - **INVALIDATED** or **MORE MAPPING NEEDED** means that task did not pass the
       validation process and needs more mapping
     - **BAD** means that task is not clear and cannot be mapped

   > Note: 'task' refers to each section of the map enclosed in the dotted
   > lines and each task has a corresponding number tag.

   ![image](https://github.com/user-attachments/assets/280fd927-b71e-4336-a89a-1672e8de687b)

   - To begin mapping, click on a task closest to you that has the color
     code associated with **READY** and change it's status from **READY**
     to **LOCKED FOR MAPPING**. Remember to take note of the number tag.
   - Scroll to the bottom of the page. The **ACTIVITIES** tab shows the
     tasks either **LOCKED FOR MAPPING**, **BAD** or **LOCKED FOR
     VALIDATION**. You can search for tasks with the status mentioned
     using the number tag associated with each task.

4. Use the QR code to start mapping the selected task using the ODK Collect app
   on your mobile phone.
5. Install and open the ODK Collect app on your phone.
6. Set up the project details by scanning the QR code provided.
7. Once the project is set up in the app, start a new form based on the selected
   form from the project setup.
8. Fill in the questionnaires and collect data for the field mapping exercise.
9. Save and send the completed form to the server.
10. After completing the assigned task, go back to the project platform on FMTM
    and mark it as fully mapped.

## Steps to Create an organisation

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

## Steps to view your submissions and infographics

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

## Steps to Edit project details

1. Users can also edit a few fields after project creation like basic
   details like name, description, instructions as well as XLS form.

2. Go to the respective project you want to edit. Click on the
   manage button to edit basic details and XLS form.

   ![image](https://github.com/user-attachments/assets/a3225885-c6cd-4fa9-9352-ccd4a8709eff)

## Help and Support

If you encounter any issues or need assistance while using FMTM, you can access
the following resources:

- Check the [FAQs][21] .
- Ask your doubts in the [Slack channel: #field-mapping-tasking-manager][22]

## Thank you

We are excited to have you join our community of passionate mappers and
volunteers. FMTM is a powerful platform developed by the Humanitarian
OpenStreetMap Team (HOT) to facilitate mapping projects for disaster response,
humanitarian efforts, and community development.

With FMTM, you have the opportunity to make a real impact by mapping areas that
are in need of support. Your contributions help create detailed and up-to-date
maps that aid organizations and communities in their efforts to respond to
crises, plan infrastructure, and improve the lives of people around the world.

Whether you are a seasoned mapper or new to the world of mapping, FMTM provides
a user-friendly interface and a range of tools to make your mapping experience
smooth and rewarding. You can create tasks, collaborate with other volunteers,
and contribute to ongoing projects that align with your interests and expertise.

By mapping with FMTM, you are joining a global community of dedicated
individuals who share a common goal of using open data to make a positive
difference. Together, we can create a more resilient and inclusive world.

Explore the projects, join tasks, and contribute your skills to help us build
accurate and comprehensive maps. Don't hesitate to ask questions, seek
guidance, and engage with fellow mappers through our forums and communication
channels.

Thank you for being part of FMTM. Your mapping efforts are invaluable, and we
appreciate your commitment to making a difference.

Happy mapping!

The FMTM Team

[9]: https://tasks.hotosm.org/learn/map "If you are new to mapping"
[10]: https://docs.getodk.org/central-install-digital-ocean/ "Account on ODK Central Server"
[11]: https://fmtm.hotosm.org/ "fmtm"
[21]: https://docs.fmtm.dev/faq "FAQs"
[22]: https://hotosm.slack.com/archives/C04PCBFDEGN "Slack channel: #field-mapping-tasking-manager"
