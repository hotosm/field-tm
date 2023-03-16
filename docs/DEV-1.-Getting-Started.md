# Overview

The FMTM codebase consists of:

- An API backend in FastAPI (code in: `src/backend`)
- A frontend website (soon to be a PWA) in react (code in: `src/frontend`)

<img src="https://github.com/hotosm/fmtm/blob/main/images/dataflow.png?raw=true"  width=800 height= 800>

## Prerequisites for Contribution

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

Make your cotribution, run tests where needed and save.

### 7. Add changes

Add the changes you've made using the following command:

`git add <file-name>`

Make sure you replace `<file-name>` with the name of the file you made changes to.

### 8. Commit and push

Once you've added changes, commit them to your local branch using the following command:

`git commit -m "Add feature"`

Make sure to write a descriptive commit message that explains the changes you've made. Then, push your changes to your forked repository using the following command:

`git push origin branch-name`

> Note: After a PR has been approved and merged, if it is not in use, delete the branch both locally and remotely with the following command:
> `git branch -d branch-name` to delete locally
> `git push origin --delete branch-name` to delete remotely.
> Otherwise we get buried in dead branches we don't need.

### 9. Submit a pull request

Go to your forked repository on GitHub and click the "New pull request" button.  
Select the branch that contains your changes, then click "Create pull request".  
This will open a new pull request in the fmtm repository, where you can describe your changes and request that they be merged into the main codebase.

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

4. Now Copy your Client ID and Client Secret. Put them in the `OSM_CLIENT_ID` and `OSM_CLIENT_SECRET` of your `.env` file

### 2. Create an `.env` File

Environmental variables are used throughout this project. To get started, create `.env` file in the top level dir, Sample is `.env.example`

    cp .env.example .env

Your env should look like this

    ### ODK Central ###
    ODK_CENTRAL_URL=https://central-proxy
    ODK_CENTRAL_USER=`<any_valid_email_address>`
    ODK_CENTRAL_PASSWD=`<password_of_central_user>`

    ### FMTM ###
    # DEBUG=True
    # LOG_LEVEL=DEBUG
    API_URL=http://127.0.0.1:8000
    FRONTEND_MAIN_URL=http://localhost:8080
    FRONTEND_MAP_URL=http://localhost:8081
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

## Verify Setup

### Check Deployment

For details on how to run this project locally for development, please look at: [DEV 2. Backend](https://github.com/hotosm/fmtm/wiki/DEV-2.-Backend)

### Check Authentication

Once you have deployed, you will need to check that you can properly authenticate.

1.  Navigate to `API_URL/docs`

    Three endpoints are responsible for oauth
    <img width="698" alt="image" src="https://user-images.githubusercontent.com/36752999/216319601-949c4262-782f-4da4-ae26-dac81c141403.png">

2.  Hit `/auth/osm_login/` : This will give you the Login URL where you can supply your osm username/password

    Response should be like this :

        {"login_url": "https://www.openstreetmap.org/oauth2/authorize/?response_type=code&client_id=xxxx"}

    Now Copy your login_url and hit it in new tab, and you will be redirected to OSM for your LOGIN. Give FMTM the necessary permission

    After successful login, you will get your `access_token` for FMTM Copy it and now you can use it for rest of the endpoints that need authorizations

3.  Check your access token: Hit `/auth/me/` and pass your `access_token` You should get your osm id, username and profile picture id

# Start Developing

Don't forget to review [Contribution](https://github.com/hotosm/fmtm/wiki/Contribution) guidelines and our [Code of Conduct](https://github.com/hotosm/fmtm/wiki/Code-of-Conduct) before contributing!
