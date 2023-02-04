### A FastAPI Project

For more information on FMTM development, see INSTALL.md

### Setup

## OSM OAUTH 2.0 Setup

-   Login to OSM , Click on My Settings and register your local fmtm backend app to Oauth2applications 

-   Put your login redirect url as `http://127.0.0.1:8000/auth/callback/` , For Production replace the URL as production API Url 

    <img width="716" alt="image" src="https://user-images.githubusercontent.com/36752999/216319298-1444a62f-ba6b-4439-bb4f-2075fdf03291.png">

    Rightnow read user preferences permission is enough later on fmtm may need permission for modify the map option which should be updated on OSM_SCOPE     variable on .env , Keep read_prefs for now 

-   Now Copy your Client ID , Client Secret and put it to `.env`

-   Generate a Secret Key for you application (You can use any secure third party secret key generator) , For Development you can put random keys

## Create .env file in Backend dir , Sample is `.env copy`

Your env should look like this 

    OSM_CLIENT_ID=
    OSM_CLIENT_SECRET=
    OSM_URL=https://www.openstreetmap.org
    OSM_SCOPE=read_prefs
    OSM_LOGIN_REDIRECT_URI=http://127.0.0.1:8000/auth/callback/
    OSM_SECRET_KEY=
    DB_URL=postgresql://{db_username}:{db_password}@{host_server}:{db_server_port}/{database_name}

## Install Requirements

    pip install -r requirements.txt

## Start Uvicorn Server

    uvicorn main:api --reload 

## Check Authentication

-   Navigate to `API_URL/docs`

    Three endpoints are responsible for oauth 
    <img width="698" alt="image" src="https://user-images.githubusercontent.com/36752999/216319601-949c4262-782f-4da4-ae26-dac81c141403.png">
-   Hit `/auth/osm_login/` : This will give you the Login URL where you can supply your osm username/password 

     Response should be like this : 

        {"login_url": "https://www.openstreetmap.org/oauth2/authorize/?response_type=code&client_id=xxxx"}

     Now Copy your login_url and hit it in new tab , you will be redirected to OSM for your LOGIN . Give FMTM necessary permission 

     After successfull login , you will get your `access_token` for FMTM Copy it and now you can use it for rest of the endpoints that needs authorizations 
     
-   Check your access token : Hit `/auth/me/` and pass your `access_token` You should get your osm id , username and profile picture id 

## Implement authorization on other endpoints

-   import `login_required` from `auth` module  , you can use it as decorator or use fastapi `Depends(login_required)` on endpoints 
