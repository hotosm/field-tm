### A FastAPI Project 
### Setup 
## OSM OAUTH 2.0 Setup 
- Login to OSM , Click on My Settings and register your local fmtm backend app to Oauth2applications 
- Put your login redirect url as ```http://127.0.0.1:8000/auth/callback/``` , For Production replace the URL as production API Url 
- Now Copy your Client ID , Client Secret and put it to ```.env```
- Generate a Secret Key for you application (You can use any secure third party secret key generator) , For Development you can put random keys

## Create .env file in Backend dir , Sample is ```.env copy```
Your env should look like this 
```
OSM_CLIENT_ID=
OSM_CLIENT_SECRET=
OSM_URL=https://www.openstreetmap.org
OSM_SCOPE=read_prefs
OSM_LOGIN_REDIRECT_URI=http://127.0.0.1:8000/auth/callback/
OSM_SECRET_KEY=
DB_URL=postgresql://{db_username}:{db_password}@{host_server}:{db_server_port}/{database_name}
```

## Install Requirements 

```
pip install -r requirements.txt
```

## Start Uvicorn Server 

```
uvicorn main:api --reload 
```