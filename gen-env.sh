#!/bin/bash
echo "Generate dotenv config for FMTM"

echo "Reading .env.example"
source .env.example

DOTENV_NAME=.env

if [ -f "${DOTENV_NAME}" ]
then
    echo "WARNING: ${DOTENV_NAME} file already exists."
    echo "This script will overwrite the content of this file."
    until [ "$conf" = "y" -o "$conf" = "n" ]
    do
        read -e -p "Do you want to overwrite it? y/n " conf
        if [ "$conf" = "y" ]
        then
            conf=""
            break
        elif [ "$conf" = "n" ]
        then
            echo "Aborting."
            exit 0
        else 
            echo "Invalid input!"
        fi
    done
fi

# Debug
echo
echo "Is this a development deployment?"
while true
do
    read -e -p "Enter y for development, anything else to continue: " debug

    if [ "$debug" = "y" ]
    then
        DEBUG=True
        LOG_LEVEL="DEBUG"
        echo "Using debug configuration."
    else 
        DEBUG=False
        LOG_LEVEL="INFO"
        break
    fi
    break
done

# External ODKCentral Creds
echo
echo "Do you want to use an external ODKCentral?"
while true
do
    read -e -p "Enter y for external, anything else to continue: " externalodk

    if [ "$externalodk" = "y" ]
    then
        EXTERNAL_ODK="True"
        echo "Using external ODKCentral."
    fi
    break
done

if [ "$EXTERNAL_ODK" = "True" ]
then
    echo
    echo "Please enter the ODKCentral URL."
    read -e -p "ODKCentral URL: " ODK_CENTRAL_URL

    echo "Please enter the ODKCentral User."
    read -e -p "ODKCentral User: " ODK_CENTRAL_USER

    echo "Please enter the ODKCentral Password."
    read -e -p "ODKCentral Password: " ODK_CENTRAL_PASSWD
fi

# External DB Creds
echo
echo "Do you want to use an external database?"
while true
do
    read -e -p "Enter y for external, anything else to continue: " externaldb

    if [ "$externaldb" = "y" ]
    then
        EXTERNAL_DB="True"
        echo "Using external database."
    fi
    break
done

if [ "$EXTERNAL_DB" = "True" ]
then
    echo
    echo "Please enter the database host."
    read -e -p "FMTM DB Host: " FMTM_DB_HOST

    echo "Please enter the database name."
    read -e -p "FMTM DB Name: " FMTM_DB_NAME

    echo "Please enter the database user."
    read -e -p "FMTM DB User: " FMTM_DB_USER

    echo "Please enter the database password."
    read -e -p "FMTM DB Password: " FMTM_DB_PASSWORD
fi

echo
echo "Do you want access FMTM securely over https?"
echo "**If yes, you need to provide valid domain names with certificates later.**"
while true
do
    read -e -p "Enter y for https, anything else for http: " https
    
    if [ "$https" = "y" ]
    then
        echo "Using https."
        URL_SCHEME="https"
    fi
    break
done

# API
echo
echo "Enter the FMTM API URL."
echo "If you have a valid domain name, enter it here."
while true
do
    read -e -p "Enter d for default 127.0.0.1:8000, else your IP/domain: " api_url
    
    if [ "$api_url" != "d" ]
    then
        echo "Using $API_URL"
        break
    elif [ "$api_url" = "" ]
    then
        echo "Invalid input!"
    else 
        echo "Using $api_url"
        API_URL="api_url"
        break
    fi
done

# FRONTEND MAIN
echo
echo "Enter the FMTM Main Frontend URL."
echo "If you have a valid domain name, enter it here."
while true
do
    read -e -p "Enter d for default 127.0.0.1:8080, else your IP/domain: " frontend_url
    
    if [ "$frontend_url" != "d" ]
    then
        echo "Using $FRONTEND_MAIN_URL"
        break
    elif [ "$api_url" = "" ]
    then
        echo "Invalid input!"
    else 
        echo "Using $FRONTEND_MAIN_URL"
        FRONTEND_MAIN_URL="frontend_url"
        break
    fi
done

# FRONTEND MAP
echo
echo "Enter the FMTM Map Frontend URL."
echo "If you have a valid domain name, enter it here."
while true
do
    read -e -p "Enter d for default 127.0.0.1:8080, else your IP/domain: " frontend_map_url
    
    if [ "$frontend_map_url" != "d" ]
    then
        echo "Using $FRONTEND_MAP_URL"
        break
    elif [ "$api_url" = "" ]
    then
        echo "Invalid input!"
    else 
        echo "Using $FRONTEND_MAP_URL"
        FRONTEND_MAP_URL="frontend_map_url"
        break
    fi
done

echo
echo "Please enter your OSM authentication details"
read -e -p "Client ID: " OSM_CLIENT_ID
read -e -p "Client Secret: " OSM_CLIENT_SECRET
read -e -p "Secret Key: " OSM_SECRET_KEY
echo "Login redirect URI (default http://127.0.0.1:8080/osmauth/): "
while true
do
    read -e -p "Enter a URI, or nothing for default: " auth_redirect_uri
    
    if [ "$auth_redirect_uri" == "" ]
    then
        echo "Using $OSM_LOGIN_REDIRECT_URI"
        break
    else 
        echo "Using $auth_redirect_uri"
        OSM_LOGIN_REDIRECT_URI="auth_redirect_uri"
        break
    fi
done

echo
echo "Generating dotenv file ${DOTENV_NAME}"

echo "### ODK Central ###"
echo "ODK_CENTRAL_URL=${ODK_CENTRAL_URL}" >> "${DOTENV_NAME}"
echo "ODK_CENTRAL_USER=${ODK_CENTRAL_USER}" >> "${DOTENV_NAME}"
echo "ODK_CENTRAL_PASSWD=${ODK_CENTRAL_PASSWD}" >> "${DOTENV_NAME}"

echo "### Debug ###"
echo "DEBUG=${DEBUG}" >> "${DOTENV_NAME}"
echo "LOG_LEVEL=${LOG_LEVEL}" >> "${DOTENV_NAME}"

echo "### FMTM ###"
echo "URL_SCHEME=${URL_SCHEME}" >> "${DOTENV_NAME}"
echo "API_URL=${API_URL}" >> "${DOTENV_NAME}"
echo "FRONTEND_MAIN_URL=${FRONTEND_MAIN_URL}" >> "${DOTENV_NAME}"
echo "FRONTEND_MAP_URL=${FRONTEND_MAP_URL}" >> "${DOTENV_NAME}"

echo "### OSM ###"
echo "OSM_CLIENT_ID=${OSM_CLIENT_ID}" >> "${DOTENV_NAME}"
echo "OSM_CLIENT_SECRET=${OSM_CLIENT_SECRET}" >> "${DOTENV_NAME}"
echo "OSM_URL=${OSM_URL}" >> "${DOTENV_NAME}"
echo "OSM_SCOPE=${OSM_SCOPE}" >> "${DOTENV_NAME}"
echo "OSM_LOGIN_REDIRECT_URI=${OSM_LOGIN_REDIRECT_URI}" >> "${DOTENV_NAME}"
echo "OSM_SECRET_KEY=${OSM_SECRET_KEY}" >> "${DOTENV_NAME}"

echo "### Database (optional) ###"
echo "CENTRAL_DB_HOST=${CENTRAL_DB_HOST}" >> "${DOTENV_NAME}"
echo "CENTRAL_DB_USER=${CENTRAL_DB_USER}" >> "${DOTENV_NAME}"
echo "CENTRAL_DB_PASSWORD=${CENTRAL_DB_PASSWORD}" >> "${DOTENV_NAME}"
echo "CENTRAL_DB_NAME=${CENTRAL_DB_NAME}" >> "${DOTENV_NAME}"

echo "FMTM_DB_HOST=${FMTM_DB_HOST}" >> "${DOTENV_NAME}"
echo "FMTM_DB_USER=${FMTM_DB_USER}" >> "${DOTENV_NAME}"
echo "FMTM_DB_PASSWORD=${FMTM_DB_PASSWORD}" >> "${DOTENV_NAME}"
echo "FMTM_DB_NAME=${FMTM_DB_NAME}" >> "${DOTENV_NAME}"

echo "Completed dotenv file generation"
exit 0
