# Overview
- [Prerequisites for Contribution](#prerequisites)

- [Titles](#titles)

The basic setup here is::point_down:

## ODK Collect

A mobile data collection tool that functions on almost all Android phones. Field mappers use ODK Collect to select features such as buildings or amenities, and fill out forms with survey questions to collect attributes or data about those features (normally at least some of these attributes are intended to become OSM tags associated with those features).

The ODK Collect app connects to a back-end server (in this case ODK Central), which provides the features to be mapped and the survey form definitions.

## ODK Central server

An ODK Central server that functions as the back end for the field data collectors' ODK Collect apps on their Android phones. Devs must have access to an ODK Central server with a username and password granting admin credentials.

[Here are the instructions for setting up an ODK Central server on Digital Ocean](https://docs.getodk.org/central-install-digital-ocean/) (it's very similar on AWS or whatever)


# Titles 

### Title 1
### Title 2

	Title 1
	========================
	Title 2 
	------------------------

# Title 1
## Title 2
### Title 3
#### Title 4
##### Title 5
###### Title 6

    # Title 1
    ## Title 2
    ### Title 3    
    #### Title 4
    ##### Title 5
    ###### Title 6    

## Field Mapping Tasking Manager Web App

The FMTM web app is a Python/Flask/Leaflet app that serves as a frontend for the ODK Central server, using the [ODK Central API](https://odkcentral.docs.apiary.io/#) to allocate specific areas/features to individual mappers, and receive their data submissions.

![1](https://github.com/hotosm/fmtm/assets/97789856/305be31a-96b4-42df-96fc-6968e9bd4e5f)

The FMTM codebase consists of:

- An API backend in FastAPI (code in: `src/backend`)
- A frontend website (soon to be a PWA) in react (code in: `src/frontend`)

### Manager Web Interface (with PC browser-friendlymap view)

A computer-screen-optimized web app that allows Campaign Managers to:

- Select AOIs
- Choose task-splitting schemes
- Provide instructions and guidance specific to the project
- View areas that are at various stages of completion
- Provide a project-specific URL that field mappers can access from their mobile phones to select and map tasks.

### Steps to create a project in FMTM
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

 - __Please watch the video below for more details__:point_down:
 

<!-- <video src="https://github.com/hotosm/fmtm/assets/97789856/8b63d8b5-2d13-4e54-8ddb-c262b0745b4f" align="centre"> -->
<!--        -->
https://github.com/hotosm/fmtm/assets/97789856/8b63d8b5-2d13-4e54-8ddb-c262b0745b4f








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

 Ideally with a link that opens ODK Collect directly from the browser, but if that's hard, the fallback is downloading a QR code and importing it into ODK Collect.

![5](https://github.com/hotosm/fmtm/assets/97789856/9343a4bc-462c-44af-af93-8a67907837b3)

## Prerequisites 

### 1. Review documentation

Don't forget to review the [Contribution](https://github.com/hotosm/fmtm/wiki/Contribution) guidelines and our [Code of Conduct](https://github.com/hotosm/fmtm/wiki/Code-of-Conduct) before contributing!
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

## Development: Setup Your Local Environment

These steps are essential to run and test your code!

### 1. Setup OSM OAUTH 2.0

The FMTM uses OAUTH2 with OSM to authenticate users. To properly configure your FMTM project, you will need to create keys for OSM.

1. [Login to OSM](https://www.openstreetmap.org/login) (_If you do not have an account yet, click the signup button at the top navigation bar to create one_). Click the drop down arrow on the extreme right of the navigation bar and select My Settings.

2. Register your local fmtm backend app to OAuth 2 applications. Put your login redirect url as `http://127.0.0.1:8000/auth/callback/`, For Production replace the URL as production API Url

> Note: `127.0.0.1` is required instead of `localhost` due to OSM restrictions.

<img width="716" alt="image" src="https://user-images.githubusercontent.com/36752999/216319298-1444a62f-ba6b-4439-bb4f-2075fdf03291.png">

3. Right now read user preferences permission is enough later on fmtm may need permission to modify the map option which should be updated on OSM_SCOPE variable on .env , Keep read_prefs for now.

4. Now Copy your Client ID and Client Secret. Put them in the `OSM_CLIENT_ID` and `OSM_CLIENT_SECRET` field of your `.env` file

### 2. Create an `.env` File

Environmental variables are used throughout this project. To get started, create `.env` file in the top level dir, Sample is `.env.example`

    cp .env.example .env

Your env should look like this:

```dotenv
### ODK Central ###
ODK_CENTRAL_URL=https://central-proxy
ODK_CENTRAL_USER=`<any_valid_email_address>`
ODK_CENTRAL_PASSWD=`<password_of_central_user>`

### FMTM ###
# DEBUG=True
# LOG_LEVEL=DEBUG
URL_SCHEME=http
API_URL=127.0.0.1:8000
FRONTEND_MAIN_URL=localhost:8080
FRONTEND_MAP_URL=localhost:8081
# API_PREFIX=/api

### OSM ###
OSM_CLIENT_ID=`<OSM_CLIENT_ID_FROM_ABOVE>`
OSM_CLIENT_SECRET=`<OSM_CLIENT_SECRET_FROM_ABOVE>`
OSM_URL=https://www.openstreetmap.org
OSM_SCOPE=read_prefs
OSM_LOGIN_REDIRECT_URI=http://127.0.0.1:8000/auth/callback/
OSM_SECRET_KEY=<random_key_for_development>

### Database (optional) ###
CENTRAL_DB_HOST=central-db
CENTRAL_DB_USER=odk
CENTRAL_DB_PASSWORD=odk
CENTRAL_DB_NAME=odk

FMTM_DB_HOST=fmtm-db
FMTM_DB_USER=fmtm
FMTM_DB_PASSWORD=fmtm
FMTM_DB_NAME=fmtm'
```

> Note: If extra cors origins are required for testing, the variable `EXTRA_CORS_ORIGINS` is a set of comma separated strings, e.g. <http://localhost:7050,http://localhost:7051>

## Verify Setup

### Check Deployment

For details on how to run this project locally for development, please look at: [DEV 2. Backend](https://github.com/hotosm/fmtm/wiki/DEV-2.-Backend)

### Check Authentication

Once you have deployed, you will need to check that you can properly authenticate.

1. Navigate to `http://127.0.0.1:8000/docs`

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

# Start Developing

Don't forget to review [Contribution](https://github.com/hotosm/fmtm/wiki/Contribution) guidelines and our [Code of Conduct](https://github.com/hotosm/fmtm/wiki/Code-of-Conduct) before contributing!
