#!/bin/bash

DOTENV_NAME=.env
IS_TEST=false
BRANCH_NAME=

pretty_echo() {
    local message="$1"
    local length=${#message}
    local separator=""

    for ((i=0; i<length+4; i++)); do
        separator="$separator-"
    done

    echo ""
    echo "$separator"
    echo "$message"
    echo "$separator"
    echo ""
}

cleanup_and_exit() {
    echo
    echo "CTRL+C received, exiting..."
    # Add extra cleanup actions here
    exit 1
}

install_envsubst_if_missing() {
    if ! command -v curl &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y curl
    fi

    echo
    # Get a8m/envsubst (required for default vals syntax ${VAR:-default})
    # Use local version, as envsubst may be installed on system already
    if [ -f ./envsubst ]; then
        echo "envsubst already exists. Continuing."
    else
        echo "Downloading a8m/envsubst"
        echo
        curl -L "https://github.com/a8m/envsubst/releases/download/v1.2.0/envsubst-$(uname -s)-$(uname -m)" -o envsubst
        chmod +x envsubst
    fi
}

check_if_test() {
    pretty_echo "Test Deployment?"

    echo "Is this a test deployment?"
    echo
    while true; do
        read -erp "Enter 'y' if yes, anything else to continue: " test

        if [[ "$test" = "y" || "$test" = "yes" ]]; then
            IS_TEST=true
            export DEBUG=True
            export LOG_LEVEL="DEBUG"
            echo "Using debug configuration."
        else
            IS_TEST=false
            export DEBUG=False
            export LOG_LEVEL="INFO"
            break
        fi
        break
    done
}

check_existing_dotenv() {
    if [ -f "${DOTENV_NAME}" ]; then
        echo "WARNING: ${DOTENV_NAME} file already exists."
        echo "This script will overwrite the content of this file."
        echo
        printf "Do you want to overwrite file \'%s\'? y/n" "${DOTENV_NAME}"
        echo
        while true; do
            read -erp "Enter 'y' to overwrite, anything else to continue: " overwrite

            if [[ "$overwrite" = "y" || "$overwrite" = "yes" ]]; then
                return 1
            else
                echo "Continuing with existing .env file."
                return 0
            fi
        done
    fi

    return 1
}

set_deploy_env() {
    pretty_echo "Deployment Environment"

    while true; do
        echo "Which environment do you wish to run? (dev/staging/prod)"
        echo
        echo "Both dev & staging include ODK Central and S3 buckets."
        echo "For prod, it is expected you provide and external instances of:"
        echo
        echo "- ODK Central"
        echo "- S3 Buckets"
        echo
        read -erp "Enter the environment (dev/staging/prod): " environment

        case "$environment" in
            dev)
                export BRANCH_NAME="dev"
                break
                ;;
            staging)
                export BRANCH_NAME="staging"
                break
                ;;
            prod)
                export BRANCH_NAME="main"
                break
                ;;
            *)
                echo "Invalid environment name. Please enter dev, staging, or prod."
                ;;
        esac
    done
}

set_external_odk() {
    pretty_echo "External ODK Central Host"

    echo "Please enter the ODKCentral URL."
    read -erp "ODKCentral URL: " ODK_CENTRAL_URL
    echo
    export ODK_CENTRAL_URL=${ODK_CENTRAL_URL}

    set_odk_user_creds
}

set_fmtm_db_pass() {
    db_pass=$(tr -dc 'a-zA-Z0-9' </dev/urandom | head -c 50)
    export FMTM_DB_PASSWORD=${db_pass}
}

set_odk_db_pass() {
    db_pass=$(tr -dc 'a-zA-Z0-9' </dev/urandom | head -c 50)
    export ODK_DB_PASSWORD=${db_pass}
}

set_odk_user_creds() {
    pretty_echo "ODK User Credentials"

    echo "Please enter the ODKCentral Email."
    read -erp "ODKCentral Email: " ODK_CENTRAL_USER
    echo
    export ODK_CENTRAL_USER=${ODK_CENTRAL_USER}

    while true; do
        echo "Please enter the ODKCentral Password."
        echo
        echo "Note: this must be >10 characters long."
        echo
        read -erp "ODKCentral Password: " ODK_CENTRAL_PASSWD
        echo

        # Check the length of the entered password
        if [ ${#ODK_CENTRAL_PASSWD} -ge 10 ]; then
            echo "Password is at least 10 characters long. Proceeding..."
            export ODK_CENTRAL_PASSWD=${ODK_CENTRAL_PASSWD}
            break  # Exit the loop if a valid password is entered
        else
            echo "Password is too short. It must be at least 10 characters long."
            echo
        fi
    done

    # Set an API key for the webhook
    api_key=$(head -c 32 /dev/urandom | base64 | tr -d '=+/')
    export CENTRAL_WEBHOOK_API_KEY="${api_key}"
}

check_external_database() {
    pretty_echo "External Database"

    echo "Do you want to use an external database instead of local?"
    while true; do
        read -erp "Enter y for external, anything else to continue: " externaldb

        if [ "$externaldb" = "y" ]; then
            EXTERNAL_DB="True"
            echo "Using external database."
        fi
        break
    done

    if [ "$EXTERNAL_DB" = "True" ]; then
        echo
        echo "Please enter the database host."
        read -erp "Field-TM DB Host: " FMTM_DB_HOST
        echo
        export FMTM_DB_HOST=${FMTM_DB_HOST}

        echo "Please enter the database name."
        read -erp "Field-TM DB Name: " FMTM_DB_NAME
        echo
        export FMTM_DB_NAME=${FMTM_DB_NAME}

        echo "Please enter the database user."
        read -erp "Field-TM DB User: " FMTM_DB_USER
        echo
        export FMTM_DB_USER=${FMTM_DB_USER}

        echo "Please enter the database password."
        read -erp "Field-TM DB Password: " FMTM_DB_PASSWORD
        echo
        export FMTM_DB_PASSWORD=${FMTM_DB_PASSWORD}

    else
        set_fmtm_db_pass
    fi
}

set_external_s3() {
    pretty_echo "S3 Credentials"

    echo "Please enter the S3 host endpoint."
    read -erp "S3 Endpoint: " S3_ENDPOINT
    echo
    export S3_ENDPOINT=${S3_ENDPOINT}

    echo "Please enter the access key."
    read -erp "S3 Access Key: " S3_ACCESS_KEY
    echo
    export S3_ACCESS_KEY=${S3_ACCESS_KEY}

    echo "Please enter the secret key."
    read -erp "S3 Secret Key: " S3_SECRET_KEY
    echo
    export S3_SECRET_KEY=${S3_SECRET_KEY}

    if [ "$BRANCH_NAME" == "main" ]; then
        echo "Production deployments require a preconfigured S3 bucket."
        echo
        echo "The bucket should be public."
        echo
        echo "Please enter the bucket name."
        read -erp "S3 Bucket Name: " S3_BUCKET_NAME
        echo
        export S3_BUCKET_NAME=${S3_BUCKET_NAME}
    fi
}

set_minio_s3_creds() {
    access_key=$(tr -dc 'a-zA-Z0-9' </dev/urandom | head -c 50)
    export S3_ACCESS_KEY=${access_key}

    secret_key=$(tr -dc 'a-zA-Z0-9' </dev/urandom | head -c 50)
    export S3_SECRET_KEY=${secret_key}
}

set_domains() {
    pretty_echo "Field-TM Domain Name"

    echo "To run Field-TM you must own a domain name."
    while true; do
        read -erp "Enter a valid domain name you wish to run Field-TM from: " fmtm_domain

        if [ "$fmtm_domain" = "" ]; then
            echo "Invalid input!"
        else
            export FMTM_DOMAIN="${fmtm_domain}"
            break
        fi
    done


    current_ip=$(hostname -I | cut -d' ' -f1)

    echo
    echo "Using $fmtm_domain as your main domain for Field-TM."
    echo
    echo "Please ensure the following DNS entries are set:"
    echo
    echo "$fmtm_domain --> $current_ip"
    echo "api.$fmtm_domain --> $current_ip"
    echo "s3.$fmtm_domain --> $current_ip"
    echo "odk.$fmtm_domain --> $current_ip"

    echo
    read -erp "Once these DNS entries are set and valid, press ENTER to continue."

    pretty_echo "Certificates"
    echo "Field-TM will automatically generate SSL (HTTPS) certificates for your domain name."
    while true; do
        echo "Enter an email address you wish to use for certificate generation."
        read -erp "This will be used by LetsEncrypt, but for no other purpose: " cert_email

        if [ "$cert_email" = "" ]; then
            echo "Invalid input!"
        else
            export CERT_EMAIL="${cert_email}"
            break
        fi
    done
}

set_osm_credentials() {
    pretty_echo "OSM OAuth2 Credentials"

    redirect_uri="http${FMTM_DOMAIN:+s}://${FMTM_DOMAIN:-127.0.0.1:7051}/osmauth"

    echo "App credentials are generated from your OSM user profile."
    echo
    echo "If you need to generate new OAuth2 App credentials, visit:"
    echo
    echo ">   https://www.openstreetmap.org/oauth2/applications"
    echo
    echo "Set the redirect URI to: ${redirect_uri}"
    echo

    echo "Please enter your OSM authentication details"
    echo
    read -erp "Client ID: " OSM_CLIENT_ID
    echo
    read -erp "Client Secret: " OSM_CLIENT_SECRET

    export OSM_CLIENT_ID=${OSM_CLIENT_ID}
    export OSM_CLIENT_SECRET=${OSM_CLIENT_SECRET}
    secret_key=$(base64 </dev/urandom | tr -dc 'a-zA-Z0-9' | head -c 50)
    export OSM_SECRET_KEY=${secret_key}
}

check_change_port() {
    pretty_echo "Set Default Port"
    echo "The default port for local development is 7050."
    echo
    read -erp "Enter a different port if required, or nothing for default: " fmtm_port

    if [ -n "$fmtm_port" ]; then
        echo "Using $fmtm_port"
        export FMTM_DEV_PORT="$fmtm_port"
    else
        echo "Using port 7050 for Field-TM."
    fi
}

generate_dotenv() {
    pretty_echo "Generating Dotenv File"

    if [ -f ./.env.example ]; then
        echo ".env.example already exists. Continuing."

        echo "substituting variables from .env.example --> ${DOTENV_NAME}"
        ./envsubst < .env.example > ${DOTENV_NAME}
    else
        echo "Downloading .env.example from repo."
        echo
        curl -LO "https://raw.githubusercontent.com/hotosm/field-tm/${BRANCH_NAME:-dev}/.env.example"

        echo "substituting variables from .env.example --> ${DOTENV_NAME}"
        ./envsubst < .env.example > ${DOTENV_NAME}

        echo "Deleting .env.example"
        rm .env.example
    fi
}

prompt_user_gen_dotenv() {
    pretty_echo "Generate dotenv config for Field-TM"
    check_existing_dotenv
    install_envsubst_if_missing
    check_if_test

    if [ $IS_TEST != true ]; then
        set_deploy_env

        if [ "$BRANCH_NAME" == "main" ]; then
            set_external_odk
            check_external_database
            set_external_s3
        else
            set_fmtm_db_pass
            set_odk_db_pass
            set_odk_user_creds
            set_minio_s3_creds
        fi

        set_domains

    else
        check_change_port
    fi

    set_osm_credentials
    generate_dotenv

    pretty_echo "Completed dotenv file generation"
}

trap cleanup_and_exit INT
prompt_user_gen_dotenv
