# Getting Started with Field Mapping Tasking Manager

- [Overview](#overview)
  - [Introduction to Field Mapping Tasking Manager Web App](#introduction-to-field-mapping-tasking-manager-web-app)
  - [Basic Tools used](#basic-tools-used)
- [Guide for Users](#guide-for-users)
  - [Prerequisites](#prerequisites)
  - [Steps to create a project in FMTM](#steps-to-create-a-project-in-fmtm)
  - [Work on existing projects](#work-on-existing-projects)
  - [Help and Support](#help-and-support)
  - [A Thank you note for the users of FMTM](#thank-you)
- [Guide for Developers](#guide-for-developers)
  - [FMTM frontend](#fmtm-frontend)
  - [FMTM backend](#fmtm-backend)
  - [Prerequisites for Contribution](#prerequisites-for-contribution)
  - [Development: Setup Your Local Environment](#setup-your-local-environment)
  - [Verify Setup](#verify-setup)
  - [Start Developing](#start-developing)

# Overview

## Introduction to Field Mapping Tasking Manager Web App

The FMTM web app is a Python/Flask/Leaflet app that serves as a frontend for the ODK Central server, using the [ODK Central API](https://odkcentral.docs.apiary.io/#) to allocate specific areas/features to individual mappers, and receive their data submissions.

![1](https://github.com/hotosm/fmtm/assets/97789856/305be31a-96b4-42df-96fc-6968e9bd4e5f)

The FMTM codebase consists of:

- An API backend in FastAPI (code in: `src/backend`)
- A frontend website in React (code in: `src/frontend`)

### Manager Web Interface (with PC browser-friendlymap view)

A computer-screen-optimized web app that allows Campaign Managers to:

- Select AOIs
- Choose task-splitting schemes
- Provide instructions and guidance specific to the project
- View areas that are at various stages of completion
- Provide a project-specific URL that field mappers can access from their mobile phones to select and map tasks.

## Basic Tools used

### [ODK Collect](https://docs.getodk.org/collect-intro/)

A mobile data collection tool that functions on almost all Android phones. Field mappers use ODK Collect to select features such as buildings or amenities, and fill out forms with survey questions to collect attributes or data about those features (normally at least some of these attributes are intended to become OSM tags associated with those features).

The ODK Collect app connects to a back-end server (in this case ODK Central), which provides the features to be mapped and the survey form definitions.

### [ODK Central server](https://odkcentral.docs.apiary.io/#)

An ODK Central server that functions as the back end for the field data collectors' ODK Collect apps on their Android phones. Devs must have access to an ODK Central server with a username and password granting admin credentials.

[Here are the instructions for setting up an ODK Central server on Digital Ocean](https://docs.getodk.org/central-install-digital-ocean/) (it's very similar on AWS or whatever)

# Guide for Users

## Prerequisites

- Stable internet connection.
- Mapping Knowledge (Optional): While not mandatory, having some mapping knowledge can enhance your experience with FMTM. If you are new to mapping we suggest you to read [this](https://tasks.hotosm.org/learn/map)

## Steps to create a project in FMTM

- Go to [fmtm](https://fmtm.hotosm.org/) .
- If you are new then on the top right cornor click on Sign up and create an account . Else , Sign in to your existing account .
- Click the '+ CREATE NEW PROJECT' button.
- Enter the project details.

![2](https://github.com/hotosm/fmtm/assets/97789856/97c38c80-aa0e-4fe2-b8a5-f4ee43a9a63a)

- Upload Area in the GEOJSON file format.

![3](https://github.com/hotosm/fmtm/assets/97789856/680eb831-790a-48f1-8997-c20b5213909d)

- Define the tasks of the project.

![Screenshot 2023-06-07 232152](https://github.com/hotosm/fmtm/assets/97789856/b735a661-d0f6-46b8-b548-5ad7b1928480)

- Select Form .

![Screenshot 2023-06-07 232316](https://github.com/hotosm/fmtm/assets/97789856/475a6070-4897-4e84-8050-6ecf024d0095)

- Click on Submit button.

- **Please watch the video below for more details**:point_down:

<!-- <video src="https://github.com/hotosm/fmtm/assets/97789856/8b63d8b5-2d13-4e54-8ddb-c262b0745b4f" align="centre"> -->
<!--        -->

<https://github.com/hotosm/fmtm/assets/97789856/8b63d8b5-2d13-4e54-8ddb-c262b0745b4f>

## Work on existing projects

If you donot want to create a new project and wish to work on an existing project then follow the steps below:

- Go to [fmtm](https://fmtm.hotosm.org/) .
- If you are new then on the top right cornor click on Sign up and create an account . Else , Sign in to your existing account .
- Click the button **Explore Projects** .
- Select the project you can work on .
- Click on the marked area.
- Click on start mapping.

![5](https://github.com/hotosm/fmtm/assets/97789856/9343a4bc-462c-44af-af93-8a67907837b3)

## Help and Support

If you encounter any issues or need assistance while using FMTM, you can access the following resources:

- Check the [FAQs](https://hotosm.github.io/fmtm/FAQ/) .
- Ask your doubts in the [Slack channel: #fmtm-field-pilots](https://hotosm.slack.com/archives/C04PCBFDEGN)

## Thank you

We are excited to have you join our community of passionate mappers and volunteers. FMTM is a powerful platform developed by the Humanitarian OpenStreetMap Team (HOT) to facilitate mapping projects for disaster response, humanitarian efforts, and community development.

With FMTM, you have the opportunity to make a real impact by mapping areas that are in need of support. Your contributions help create detailed and up-to-date maps that aid organizations and communities in their efforts to respond to crises, plan infrastructure, and improve the lives of people around the world.

Whether you are a seasoned mapper or new to the world of mapping, FMTM provides a user-friendly interface and a range of tools to make your mapping experience smooth and rewarding. You can create tasks, collaborate with other volunteers, and contribute to ongoing projects that align with your interests and expertise.

By mapping with FMTM, you are joining a global community of dedicated individuals who share a common goal of using open data to make a positive difference. Together, we can create a more resilient and inclusive world.

Explore the projects, join tasks, and contribute your skills to help us build accurate and comprehensive maps. Don't hesitate to ask questions, seek guidance, and engage with fellow mappers through our forums and communication channels.

Thank you for being part of FMTM. Your mapping efforts are invaluable, and we appreciate your commitment to making a difference.

Happy mapping!

The FMTM Team

# Guide for Developers

## FMTM frontend

_To view details about the frontend click
[here](https://hotosm.github.io/fmtm/dev/Frontend/)_

### Field Mapper Web Interface (with mobile-friendly map view)

Ideally with a link that opens ODK Collect directly from the browser, but if that's hard, the fallback is downloading a QR code and importing it into ODK Collect.

## FMTM backend

_To in details about the backend click
[here](https://hotosm.github.io/fmtm/dev/backend/)_

A backend that converts the project parameters entered by the Campaign Manager in the Manager Web Interface into a corresponding ODK Central project. Its functions include:

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

## Prerequisites for Contribution

### 1. Review documentation

Don't forget to review the
[Contribution](https://hotosm.github.io/fmtm/CONTRIBUTING/)
guidelines and our
[Code of Conduct](https://hotosm.github.io/fmtm/CODE_OF_CONDUCT/)
before contributing!

Here are the steps to contribute to the frontend of Field Mapping Tasking Manager:

### 2. Fork the repository

Forking creates a copy of the repository in your own GitHub account.
Go to the [Field Mapping Tasking Manager repository](https://github.com/hotosm/fmtm) and click the "Fork" button in the top right corner of the page.

### 3. Navigate to your working directory

Open a terminal and navigate to the directory you want to work in using the following command:

`cd <work-dir>`

Make sure to replace `<work-dir>` with the name of your directory.

### 4. Clone the forked repository

Clone the forked repository to your local machine using the following command:

`git clone https://github.com/<your-username>/fmtm.git`

Make sure to replace `<your-username>` with your GitHub username.

### 5. Create a new branch

Create a new branch for your changes using the following command:

`git checkout -b branch-name`

Make sure to give your branch a descriptive name that reflects the changes you'll be making.

### 6. Make changes

Make your contribution, run tests where needed and save.

### 7. Add changes

Add the changes you've made using the following command:

`git add <file-name>`

Make sure you replace `<file-name>` with the name of the file you made changes to.

### 8. Commit and push

Once you've added changes, commit them to your local branch using the following command:

`git commit -m "Add feature"`

Make sure to write a descriptive commit message that explains the changes you've made. Then, push your changes to your forked repository using the following command:

`git push origin branch-name`

### 9. Submit a pull request

Go to your forked repository on GitHub and click the "Pull requests" tab.  
Change the base branch from `main` to `development`, select the branch that contains your changes from the compare branch, then click "Create pull request".  
This will open a new pull request in the fmtm repository, where you can describe your changes and request that they be merged into the main codebase.

> Note: After a PR has been approved and merged, if the branch is no longer in use, delete it both locally and remotely. Otherwise we get buried in dead branches we don't need.  
> Use the following commands:  
> Switch out of the branch you want to delete `git checkout <some-other-branch>`(_Replace `<some-other-branch>` with any other existing branch name_).  
> Delete the branch locally `git branch -d <branch-name>` and then delete the branch remotely `git push origin --delete <branch-name>`(_Replace `<branch-name>` with the name of the branch you want to delete_).

That's it! You've now contributed to the Field Mapping Tasking Manager.

## Setup Your Local Environment

These steps are essential to run and test your code!

### 1. Setup OSM OAUTH 2.0

The FMTM uses OAUTH2 with OSM to authenticate users. To properly configure your FMTM project, you will need to create keys for OSM.

1. [Login to OSM](https://www.openstreetmap.org/login) (_If you do not have an account yet, click the signup button at the top navigation bar to create one_). Click the drop down arrow on the extreme right of the navigation bar and select My Settings.

2. Register your FMTM instance to OAuth 2 applications. Put your login redirect url as `http://127.0.0.1:7051/osmauth/`, For Production replace the URL as production API Url

> Note: `127.0.0.1` is required instead of `localhost` due to OSM restrictions.

<img width="716" alt="image" src="https://user-images.githubusercontent.com/36752999/216319298-1444a62f-ba6b-4439-bb4f-2075fdf03291.png">

3. Right now read user preferences permission is enough later on fmtm may need permission to modify the map option which should be updated on OSM_SCOPE variable on .env , Keep read_prefs for now.

4. Now Copy your Client ID and Client Secret. Put them in the `OSM_CLIENT_ID` and `OSM_CLIENT_SECRET` field of your `.env` file

#### 2. Create an `.env` File

Environmental variables are used throughout this project.
To get started, create `.env` file in the top level dir,
a sample is located at `.env.example`.

This can be created interactively by running:

```bash
bash scripts/gen-env.sh
```

> Note: If extra cors origins are required for testing, the variable
> `EXTRA_CORS_ORIGINS` is a set of comma separated strings, e.g.:
> <http://fmtm.localhost:7050,http://some.other.domain>

## Verify Setup

### Check Deployment

For details on how to run this project locally for development, please look at: [Backend Docs](https://hotosm.github.io/fmtm/dev/Backend)

### Check Authentication

Once you have deployed, you will need to check that you can properly authenticate.

1. Navigate to `http://api.fmtm.localhost:7050/docs`

    Three endpoints are responsible for oauth
    <img width="698" alt="image" src="../images/endpoints_responsible_for_auth_screenshot-2023-03-26-092756.png">

2. Select the `/auth/osm_login/` endpoint, click `Try it out` and then `Execute`.  
    This would give you the Login URL where you can supply your osm username and password.

    Your response should look like this:

        {"login_url": "https://www.openstreetmap.org/oauth2/authorize/?response_type=code&client_id=xxxx"}

    Now copy and paste your login_url in a new tab. You would be redirected to OSM for your LOGIN. Give FMTM the necessary permission.

    After a successful login, you will get your `access_token` for FMTM, Copy it. Now, you can use it for rest of the endpoints that needs authorization.

3. Check your access token: Select the `/auth/me/` endpoint and click `Try it out`.  
    Pass in the `access_token` you copied in the previous step into the `access-token` field and click `Execute`. You should get your osm id, username and profile picture id.

## Start Developing

Don't forget to review the
[Contribution](https://hotosm.github.io/fmtm/CONTRIBUTING/)
guidelines and our
[Code of Conduct](https://hotosm.github.io/fmtm/CODE_OF_CONDUCT/)
before contributing!

Happy coding!

The FMTM Developer Team

## Note

To run the local development setup without ODK Central (use external server):

```bash
dc --profile no-odk up -d
```
