#!/bin/bash

set -o pipefail

# Tested for Debian 11 Bookworm & Ubuntu 22.04 LTS

# Auto accept all apt prompts
export DEBIAN_FRONTEND=noninteractive

# Global Vars
RANDOM_DIR="${RANDOM}${RANDOM}"
DOTENV_NAME=.env
OS_NAME="debian"
IS_TEST=false
BRANCH_NAME=development
COMPOSE_FILE=docker-compose.yml

heading_echo() {
    local message="$1"
    local color="${2:-blue}"
    local separator="--------------------------------------------------------"
    local sep_length=${#separator}
    local pad_length=$(( (sep_length - ${#message}) / 2 ))
    local pad=""

    case "$color" in
        "black") color_code="\e[0;30m" ;;
        "red") color_code="\e[0;31m" ;;
        "green") color_code="\e[0;32m" ;;
        "yellow") color_code="\e[0;33m" ;;
        "blue") color_code="\e[0;34m" ;;
        "purple") color_code="\e[0;35m" ;;
        "cyan") color_code="\e[0;36m" ;;
        "white") color_code="\e[0;37m" ;;
        *) color_code="\e[0m" ;;  # Default: reset color
    esac

    for ((i=0; i<pad_length; i++)); do
        pad="$pad "
    done

    echo ""
    echo -e "${color_code}$separator\e[0m"
    echo -e "${color_code}$pad$message$pad\e[0m"
    echo -e "${color_code}$separator\e[0m"
    echo ""
}

yellow_echo() {
    local text="$1"
    echo -e "\e[0;33m${text}\e[0m"
}

install_progress() {
    local pid=$1
    local delay=0.5
    local spin[0]="-"
    local spin[1]="\\"
    local spin[2]="|"
    local spin[3]="/"

    while [ "$(ps a | awk '{print $1}' | grep $pid)" ]; do
        local temp=${spin[0]}
        spin[0]=${spin[1]}
        spin[1]=${spin[2]}
        spin[2]=${spin[3]}
        spin[3]=$temp
        echo -ne "${spin[0]} Installing machinectl requirement...\r"
        sleep $delay
    done
    yellow_echo "${spin[0]} Installing machinectl requirement... Done"
}

display_logo() {
    echo 
    echo " ███████████ ██████   ██████ ███████████ ██████   ██████"
    echo "░░███░░░░░░█░░██████ ██████ ░█░░░███░░░█░░██████ ██████ "
    echo " ░███   █ ░  ░███░█████░███ ░   ░███  ░  ░███░█████░███ "
    echo " ░███████    ░███░░███ ░███     ░███     ░███░░███ ░███ "
    echo " ░███░░░█    ░███ ░░░  ░███     ░███     ░███ ░░░  ░███ "
    echo " ░███  ░     ░███      ░███     ░███     ░███      ░███ "
    echo " █████       █████     █████    █████    █████     █████"
    echo "░░░░░       ░░░░░     ░░░░░    ░░░░░    ░░░░░     ░░░░░ "
    echo
    echo "--------------------------------------------------------"
    echo "             Field Tasking Mapping Manager              "
    echo "--------------------------------------------------------"
    echo
    echo
}

cleanup_and_exit() {
    echo
    echo "CTRL+C received, exiting..."

    # Cleanup files
    rm -rf "/tmp/${RANDOM_DIR}"

    exit 1
}

check_user_not_root() {
    if [ "$(id -u)" -eq 0 ]; then
        heading_echo "WARNING" "yellow"

        yellow_echo "Current user is root."
        yellow_echo "This script must run as a non-privileged user account."
        echo

        if id "svcfmtm" &>/dev/null; then
            yellow_echo "User 'svcfmtm' found."
        else
            yellow_echo "Creating user 'svcfmtm'."
            useradd -m -d /home/svcfmtm -s /bin/bash svcfmtm 2>/dev/null
        fi

        echo
        yellow_echo "Enable login linger for user svcfmtm (docker if logged out)."
        loginctl enable-linger svcfmtm

        echo
        yellow_echo "Temporarily adding to sudoers list."
        echo "svcfmtm ALL=(ALL) NOPASSWD:ALL" | tee /etc/sudoers.d/fmtm-sudoers >/dev/null

        echo
        yellow_echo "Rerunning this script as user 'svcfmtm'."
        echo

        if ! command -v machinectl &>/dev/null; then
            # Start the installation process in the background with spinner
            ( apt-get update > /dev/null
            wait  # Wait for 'apt-get update' to complete
            apt-get install -y systemd-container --no-install-recommends > /dev/null ) &
            install_progress $!
            echo
        fi

        # Check if input is direct bash script call (i.e. ends in .sh)
        ext="$(basename "$0")"
        if [ "${ext: -3}" = ".sh" ]; then
            # User called script directly, copy to /home/svcfmtm/install.sh
            root_script_path="$(readlink -f "$0")"
            user_script_path="/home/svcfmtm/$(basename "$0")"
            cp "$root_script_path" "$user_script_path"
            chmod +x "$user_script_path"

            machinectl --quiet shell \
                --setenv=RUN_AS_ROOT=true \
                --setenv=DOCKER_HOST=${DOCKER_HOST} \
                svcfmtm@ /bin/bash -c "$user_script_path"
        else
            # User called script remotely, so do the same
            machinectl --quiet shell \
                --setenv=RUN_AS_ROOT=true \
                --setenv=DOCKER_HOST=${DOCKER_HOST} \
                svcfmtm@ /bin/bash -c "curl -fsSL https://get.fmtm.dev | bash"
        fi

        exit 0
    fi
}

check_os() {
    heading_echo "Checking Current OS"

    if [ -e /etc/os-release ]; then
        source /etc/os-release
        case "$ID" in
        debian)
            export OS_NAME=${ID}
            echo "Current OS is ${PRETTY_NAME}."
            ;;
        ubuntu)
            export OS_NAME=${ID}
            echo "Current OS is ${PRETTY_NAME}."
            ;;
        *)
            echo "Current OS is not Debian or Ubuntu. Exiting."
            exit 1
            ;;
        esac
    else
        echo "Could not determine the operating system. Exiting."
        exit 1
    fi
}

remove_old_docker_installs() {
    heading_echo "Removing Old Versions of Docker"
    packages=(
        docker.io
        docker-doc
        docker-compose
        podman-docker
        containerd
        runc
    )
    for pkg in "${packages[@]}"; do
        sudo apt-get remove "$pkg"
    done
}

install_dependencies() {
    heading_echo "Installing Dependencies"
    sudo apt-get update
    sudo apt-get install -y \
        ca-certificates \
        curl \
        gnupg \
        uidmap \
        dbus-user-session \
        slirp4netns

    if [ "$OS_NAME" = "debian" ]; then
        sudo apt-get install -y fuse-overlayfs
    fi
}

add_gpg_key() {
    heading_echo "Adding Docker GPG Key"
    sudo install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/${ID}/gpg | sudo gpg --yes --dearmor -o /etc/apt/keyrings/docker.gpg
    sudo chmod a+r /etc/apt/keyrings/docker.gpg
    echo "Done"
}

add_to_apt() {
    heading_echo "Adding Docker to Apt Source"
    echo \
        "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/${ID} \
        $(. /etc/os-release && echo $VERSION_CODENAME) stable" | \
        sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    echo "Done"
}

apt_install_docker() {
    heading_echo "Installing Docker"
    sudo apt-get update
    sudo apt-get install -y \
        docker-ce \
        docker-ce-cli \
        containerd.io \
        docker-buildx-plugin \
        docker-compose-plugin \
        docker-ce-rootless-extras
}

update_to_rootless() {
    heading_echo "Disabling Docker Service (If Running)"
    sudo systemctl disable --now docker.service docker.socket

    heading_echo "Install Rootless Docker"
    dockerd-rootless-setuptool.sh install
}

restart_docker_rootless() {
    heading_echo "Restarting Docker Service"
    echo "This is required as sometimes docker doesn't init correctly."
    systemctl --user daemon-reload
    systemctl --user restart docker
    echo
    echo "Done."
}

allow_priv_port_access() {
    heading_echo "Allowing Privileged Port Usage"
    sudo tee -a /etc/sysctl.conf <<EOF > /dev/null 2>&1
net.ipv4.ip_unprivileged_port_start=0
EOF
    sudo sysctl -p
    echo "Done"
}

update_docker_ps_format() {
    heading_echo "Updating docker ps Formatting"

    # Root user
    if [ "$RUN_AS_ROOT" = true ]; then
        sudo mkdir -p /root/.docker
        sudo touch /root/.docker/config.json
        sudo tee /root/.docker/config.json <<EOF > /dev/null 2>&1
{
    "psFormat": "table {{.ID}}\\t{{.Image}}\\t{{.Status}}\\t{{.Names}}"
}
EOF
    fi

    # svcfmtm user
    mkdir -p ~/.docker
    touch ~/.docker/config.json
    tee ~/.docker/config.json <<EOF > /dev/null 2>&1
{
    "psFormat": "table {{.ID}}\\t{{.Image}}\\t{{.Status}}\\t{{.Names}}"
}
EOF

echo "Done"
}


add_vars_to_bashrc() {
    # DOCKER_HOST must be added to the top of bashrc, as running non-interactively
    # Most distros exit .bashrc execution is non-interactive

    heading_echo "Adding DOCKER_HOST and 'dc' alias to bashrc"

    user_id=$(id -u)
    docker_host_var="export DOCKER_HOST=unix:///run/user/$user_id/docker.sock"
    dc_alias_cmd="alias dc='docker compose'"

    # Create temporary files for root and user bashrc
    tmpfile_root=$(mktemp)
    tmpfile_user=$(mktemp)

    if [ "$RUN_AS_ROOT" = true ]; then
        # Check if DOCKER_HOST is already defined in /root/.bashrc
        if ! sudo grep -q "$docker_host_var" /root/.bashrc; then
            echo "Adding DOCKER_HOST var to /root/.bashrc."
            echo "$docker_host_var" | sudo tee -a "$tmpfile_root" > /dev/null
            echo
        fi

        # Check if the 'dc' alias already exists in /root/.bashrc
        if ! sudo grep -q "$dc_alias_cmd" /root/.bashrc; then
            echo "Adding 'dc' alias to /root/.bashrc."
            echo "$dc_alias_cmd" | sudo tee -a "$tmpfile_root" > /dev/null
            echo
        fi
    fi

    # Check if DOCKER_HOST is already defined in ~/.bashrc
    if ! grep -q "$docker_host_var" ~/.bashrc; then
        echo "Adding DOCKER_HOST var to ~/.bashrc."
        echo "$docker_host_var" | tee -a "$tmpfile_user" > /dev/null
        echo
    fi

    # Check if the 'dc' alias already exists in ~/.bashrc
    if ! grep -q "$dc_alias_cmd" ~/.bashrc; then
        echo "Adding 'dc' alias to ~/.bashrc."
        echo "$dc_alias_cmd" | tee -a "$tmpfile_user" > /dev/null
        echo
    fi

    # Append the rest of the original .bashrc to the temporary file
    if [ -e ~/.bashrc ]; then
        grep -v -e "$docker_host_var" -e "$dc_alias_cmd" ~/.bashrc >> "$tmpfile_user"
    fi
    # Replace the original .bashrc with the modified file
    mv "$tmpfile_user" ~/.bashrc

    # If RUN_AS_ROOT is true, replace /root/.bashrc with the modified file
    if [ "$RUN_AS_ROOT" = true ]; then
        # Append the rest of the original /root/.bashrc to the temporary file
        if [ -e /root/.bashrc ]; then
            grep -v -e "$docker_host_var" -e "$dc_alias_cmd" /root/.bashrc >> "$tmpfile_root"
        fi

        # Replace the original /root/.bashrc with the modified file
        sudo mv "$tmpfile_root" /root/.bashrc
    fi

    echo "Setting DOCKER_HOST for the current session."
    export DOCKER_HOST=unix:///run/user/$(id -u)/docker.sock

    echo
    echo "Done"
}

install_docker() {
    heading_echo "Docker Install"

    if command -v docker &> /dev/null; then
        echo "Docker already installed: $(which docker)"
        echo "Skipping."
        return 0
    fi

    echo "Docker is required for FMTM to run."
    echo
    echo "Do you want to install Docker? (y/n)"
    echo
    read -rp "Enter 'y' to install, anything else to continue: " install_docker

    if [[ "$install_docker" = "y" ||  "$install_docker" = "yes" ]]; then
        check_os
        remove_old_docker_installs
        install_dependencies
        add_gpg_key
        add_to_apt
        apt_install_docker
        update_to_rootless
        allow_priv_port_access
        restart_docker_rootless
        update_docker_ps_format
        add_vars_to_bashrc
    else
        heading_echo "Docker is Required. Aborting." "red"
        exit 1
    fi
}

install_envsubst_if_missing() {
    if ! command -v curl &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y curl --no-install-recommends
    fi

    echo
    # Get a8m/envsubst (required for default vals syntax ${VAR:-default})
    # Use local version, as envsubst may be installed on system already
    if [ -f ./envsubst ]; then
        echo "envsubst already exists. Continuing."
    else
        echo "Downloading a8m/envsubst"
        echo
        curl -L https://github.com/a8m/envsubst/releases/download/v1.2.0/envsubst-`uname -s`-`uname -m` -o envsubst
        chmod +x envsubst
    fi
}

check_existing_dotenv() {
    if [ -f "${DOTENV_NAME}" ]
    then
        echo "WARNING: ${DOTENV_NAME} file already exists."
        echo "This script will overwrite the content of this file."
        echo
        echo "Do you want to overwrite file '"${DOTENV_NAME}"'? y/n"
        echo
        while true
        do
            read -e -p "Enter 'y' to overwrite, anything else to continue: " overwrite

            if [[ "$overwrite" = "y" || "$overwrite" = "yes" ]]
            then
                return 1
            else 
                echo "Continuing with existing .env file."
                return 0
            fi
        done
    fi

    return 1
}

check_if_test() {
    heading_echo "Test Deployment?"

    echo "Is this a test deployment?"
    echo
    while true
    do
        read -e -p "Enter 'y' if yes, anything else to continue: " test

        if [[ "$test" = "y" || "$test" = "yes" ]]
        then
            IS_TEST=true
            export DEBUG="True"
            export LOG_LEVEL="DEBUG"
            echo "Using debug configuration."
        else
            IS_TEST=false
            export DEBUG="False"
            export LOG_LEVEL="INFO"
            break
        fi
        break
    done
}

get_repo() {
    heading_echo "Getting Necessary Files"

    current_dir="${PWD}"

    if ! command -v git &>/dev/null; then
        yellow_echo "Downloading GIT."
        echo
        sudo apt-get update
        sudo apt-get install -y git --no-install-recommends
        echo
    fi

    # Files in a random temp dir
    mkdir -p "/tmp/${RANDOM_DIR}"
    cd "/tmp/${RANDOM_DIR}"

    repo_url="https://github.com/hotosm/fmtm.git"

    echo "Cloning repo $repo_url to dir: /tmp/${RANDOM_DIR}"
    echo
    git clone --branch "${BRANCH_NAME}" --depth 1 "$repo_url"

    # Check for existing .env files
    existing_dotenv=""
    if [ "${RUN_AS_ROOT}" = true ] && sudo test -f "/root/fmtm/${DOTENV_NAME}"; then
        existing_dotenv="/root/fmtm/${DOTENV_NAME}"
    elif [ -f "${current_dir}/${DOTENV_NAME}" ]; then
        existing_dotenv="${current_dir}/${DOTENV_NAME}"
    fi

    if [ -n "$existing_dotenv" ]; then
        echo
        echo "Found existing dotenv file."
        echo
        echo "Copying $existing_dotenv --> /tmp/${RANDOM_DIR}/fmtm/${DOTENV_NAME}"
        if [ "${RUN_AS_ROOT}" = true ]; then
            sudo cp "$existing_dotenv" "/tmp/${RANDOM_DIR}/fmtm/"
        else
            cp "$existing_dotenv" "/tmp/${RANDOM_DIR}/fmtm/"
        fi
    fi
}

set_deploy_env() {
    heading_echo "Deployment Environment"

    while true
    do
        echo "Which environment do you wish to run? (dev/staging/prod)"
        echo
        echo "Both dev & staging include ODK Central and S3 buckets."
        echo "For prod, it is expected you provide and external instances of:"
        echo
        echo "- ODK Central"
        echo "- S3 Buckets"
        echo
        read -e -p "Enter the environment (dev/staging/prod): " environment

        case "$environment" in
            dev)
                BRANCH_NAME="development"
                ;;
            staging)
                BRANCH_NAME="staging"
                ;;
            prod)
                BRANCH_NAME="main"
                ;;
            *)
                echo "Invalid environment name. Please enter dev, staging, or prod."
                ;;

        esac

        export GIT_BRANCH="${BRANCH_NAME}"
        COMPOSE_FILE="docker-compose.${BRANCH_NAME}.yml"
        break
    done
}

set_external_odk() {
    heading_echo "External ODK Central Host"

    echo "Please enter the ODKCentral URL."
    read -e -p "ODKCentral URL: " ODK_CENTRAL_URL
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
    heading_echo "ODK User Credentials"

    echo "Please enter the ODKCentral Email."
    read -e -p "ODKCentral Email: " ODK_CENTRAL_USER
    echo
    export ODK_CENTRAL_USER=${ODK_CENTRAL_USER}

    echo "Please enter the ODKCentral Password."
    echo
    yellow_echo "Note: this must be >10 characters long."
    while true; do
        echo
        read -e -p "ODKCentral Password: " ODK_CENTRAL_PASSWD
        echo

        # Check the length of the entered password
        if [ ${#ODK_CENTRAL_PASSWD} -ge 10 ]; then
            export ODK_CENTRAL_PASSWD=${ODK_CENTRAL_PASSWD}
            break
        else
            yellow_echo "Password is too short. It must be at least 10 characters long."
        fi
    done
}

check_external_database() {
    heading_echo "External Database"

    echo "Do you want to use an external database instead of local?"
    echo
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
        echo
        export FMTM_DB_HOST=${FMTM_DB_HOST}

        echo "Please enter the database name."
        read -e -p "FMTM DB Name: " FMTM_DB_NAME
        echo
        export FMTM_DB_NAME=${FMTM_DB_NAME}

        echo "Please enter the database user."
        read -e -p "FMTM DB User: " FMTM_DB_USER
        echo
        export FMTM_DB_USER=${FMTM_DB_USER}

        echo "Please enter the database password."
        read -e -p "FMTM DB Password: " FMTM_DB_PASSWORD
        echo
        export FMTM_DB_PASSWORD=${FMTM_DB_PASSWORD}

    else
        set_fmtm_db_pass
    fi
}

set_external_s3() {
    heading_echo "S3 Credentials"

    echo "Please enter the S3 host endpoint."
    read -e -p "S3 Endpoint: " S3_ENDPOINT
    echo
    export S3_ENDPOINT=${S3_ENDPOINT}

    echo "Please enter the access key."
    read -e -p "S3 Access Key: " S3_ACCESS_KEY
    echo
    export S3_ACCESS_KEY=${S3_ACCESS_KEY}

    echo "Please enter the secret key."
    read -e -p "S3 Secret Key: " S3_SECRET_KEY
    echo
    export S3_SECRET_KEY=${S3_SECRET_KEY}

    if [ "$BRANCH_NAME" = "main" ]; then
        yellow_echo "Production deployments require a preconfigured S3 bucket."
        echo
        yellow_echo "The bucket should be public."
        echo
        echo "Please enter the bucket name."
        read -e -p "S3 Bucket Name: " S3_BUCKET_NAME
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
    heading_echo "FMTM Domain Name"

    echo "To run FMTM you must own a domain name."
    while true
    do
        read -e -p "Enter a valid domain name you wish to run FMTM from: " fmtm_domain

        if [ "$fmtm_domain" = "" ]
        then
            echo "Invalid input!"
        else
            export FMTM_DOMAIN="${fmtm_domain}"
            break
        fi
    done


    current_ip=$(hostname -I | cut -d' ' -f1)

    echo
    echo "Using $fmtm_domain as your main domain for FMTM."
    echo
    yellow_echo "Please ensure the following DNS entries are set:"
    echo
    yellow_echo "$fmtm_domain --> $current_ip"
    yellow_echo "api.$fmtm_domain --> $current_ip"

    if [ "$BRANCH_NAME" != "main" ]
    then
        yellow_echo "s3.$fmtm_domain --> $current_ip"
        yellow_echo "odk.$fmtm_domain --> $current_ip"
    fi

    echo
    read -e -p "Once these DNS entries are set and valid, press ENTER to continue." valid

    heading_echo "Certificates"
    echo "FMTM will automatically generate SSL (HTTPS) certificates for your domain name."
    echo
    while true
    do
        echo "Enter an email address you wish to use for certificate generation."
        echo "This will be used by LetsEncrypt, but for no other purpose."
        echo
        read -e -p "Email: " cert_email

        if [ "$cert_email" = "" ]
        then
            echo "Invalid input!"
        else
            export CERT_EMAIL="${cert_email}"
            break
        fi
    done
}

set_osm_credentials() {
    heading_echo "OSM OAuth2 Credentials"

    redirect_uri="http${FMTM_DOMAIN:+s}://${FMTM_DOMAIN:-127.0.0.1:7051}/osmauth/"

    yellow_echo "App credentials are generated from your OSM user profile."
    echo
    yellow_echo "If you need to generate new OAuth2 App credentials, visit:"
    echo
    yellow_echo ">   https://www.openstreetmap.org/oauth2/applications"
    echo
    yellow_echo "Set the redirect URI to: ${redirect_uri}"
    echo

    echo "Please enter your OSM authentication details"
    echo
    read -e -p "Client ID: " OSM_CLIENT_ID
    echo
    read -e -p "Client Secret: " OSM_CLIENT_SECRET

    export OSM_CLIENT_ID=${OSM_CLIENT_ID}
    export OSM_CLIENT_SECRET=${OSM_CLIENT_SECRET}
    secret_key=$(tr -dc 'a-zA-Z0-9' </dev/urandom | head -c 50)
    export OSM_SECRET_KEY=${secret_key}
}

check_change_port() {
    heading_echo "Set Default Port"
    echo "The default port for local development is 7050."
    echo
    read -e -p "Enter a different port if required, or nothing for default: " fmtm_port

    if [ -n "$fmtm_port" ]; then
        echo "Using $fmtm_port"
        export FMTM_DEV_PORT="$fmtm_port"
    else
        echo "Using port 7050 for FMTM."
    fi
}

generate_dotenv() {
    heading_echo "Generating Dotenv File"

    if [ -f ./.env.example ]; then
        echo ".env.example already exists. Continuing."

        echo
        echo "substituting variables from .env.example --> ${DOTENV_NAME}"
        ./envsubst < .env.example > ${DOTENV_NAME}
    else
        echo "Downloading .env.example from repo."
        echo
        curl -LO "https://raw.githubusercontent.com/hotosm/fmtm/${BRANCH_NAME:-development}/.env.example"

        echo
        echo "substituting variables from .env.example --> ${DOTENV_NAME}"
        ./envsubst < .env.example > ${DOTENV_NAME}

        echo
        echo "Deleting .env.example"
        rm .env.example
    fi

    heading_echo "Completed Dotenv File Generation." "green"
    echo "File ${DOTENV_NAME} content:"
    echo
    cat ${DOTENV_NAME}
    echo
    if [ "${RUN_AS_ROOT}" = true ] && sudo test ! -f "/root/fmtm/${DOTENV_NAME}"; then
        echo "Copying generated dotenv to /root/fmtm/${DOTENV_NAME}"
        cp "${DOTENV_NAME}" "/root/fmtm/${DOTENV_NAME}" || true
    elif [ ! -f "/home/svcfmtm/${DOTENV_NAME}" ]; then
        echo "Copying generated dotenv to /home/svcfmtm/fmtm/${DOTENV_NAME}"
        cp "${DOTENV_NAME}" "/home/svcfmtm/fmtm/${DOTENV_NAME}" || true
    fi
}

prompt_user_gen_dotenv() {
    heading_echo "Generate dotenv config for FMTM"

    # Exit if user does not overwrite existing dotenv
    if check_existing_dotenv; then
        return
    fi

    install_envsubst_if_missing

    if [ $IS_TEST != true ]; then
        if [ "$BRANCH_NAME" = "main" ]; then
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
}

run_compose_stack() {
    # Workaround if DOCKER_HOST is missed (i.e. docker just installed)
    if [ -z "$DOCKER_HOST" ]; then
        export DOCKER_HOST=unix:///run/user/$(id -u)/docker.sock
    fi

    heading_echo "Pulling Required Images"
    docker compose -f ${COMPOSE_FILE} pull
    heading_echo "Building Frontend Image"
    docker compose -f ${COMPOSE_FILE} build ui

    heading_echo "Starting FMTM"
    docker compose -f ${COMPOSE_FILE} up \
        --detach --remove-orphans --force-recreate
}

final_output() {
    # Source env vars
    . .env

    proto="http"
    suffix=""

    if [ "$IS_TEST" != true ]; then
        proto="https"
    else
        suffix=":${FMTM_DEV_PORT:-7050}"
    fi

    heading_echo "FMTM Setup Complete"
    heading_echo "Services" "green"
    echo "Frontend:     ${proto}://${FMTM_DOMAIN}${suffix}"
    echo "API:          ${proto}://api.${FMTM_DOMAIN}${suffix}"
    echo "S3 Buckets:   ${proto}://s3.${FMTM_DOMAIN}${suffix}"
    echo "ODK Central:  ${proto}://odk.${FMTM_DOMAIN}${suffix}"
    heading_echo "Inspect Containers" "green"
    echo "To login as svcfmtm and inspect the containers, run:"
    echo
    echo "$ machinectl shell svcfmtm@"
    echo "$ docker ps"
    echo
    echo "Alternatively, to run as the current user:"
    echo
    echo "$ export DOCKER_HOST=unix:///run/user/$(id -u svcfmtm)/docker.sock"
    echo "$ docker ps"
    echo
    heading_echo "ODK Central Credentials" "green"
    echo "URL:          ${ODK_CENTRAL_URL}"
    echo "Email:        ${ODK_CENTRAL_USER}"
    echo "Password:     ${ODK_CENTRAL_PASSWD}"
    echo
}

install_fmtm() {
    check_user_not_root
    display_logo

    trap cleanup_and_exit INT
    install_docker

    check_if_test
    if [ $IS_TEST != true ]; then
        set_deploy_env
    fi

    get_repo
    # Work in generated temp dir
    local repo_dir="/tmp/${RANDOM_DIR}/fmtm"
    cd "${repo_dir}"

    if [ -f "${repo_dir}/${DOTENV_NAME}" ]; then
        heading_echo "Skip Dotenv Generation"
        echo "Using existing dotenv file."
    else
        prompt_user_gen_dotenv
    fi
    
    run_compose_stack
    final_output

    if [[ "$RUN_AS_ROOT" = true ]]; then
        # Remove from sudoers
        sudo rm /etc/sudoers.d/fmtm-sudoers
    fi

    # Cleanup files
    if [[ "$IS_TEST" != true ]]; then
        rm -rf "/tmp/${RANDOM_DIR:-tmp}"
    fi

}

install_fmtm
