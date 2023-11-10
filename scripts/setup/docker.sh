#!/bin/bash

# Tested for Debian 11 Bookworm & Ubuntu 22.04 LTS
# Note: this script must be run as a non-root user
# Note: The user must be logged in directly (not via su)

OS_NAME="debian"

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

check_os() {
    pretty_echo "Checking Current OS"

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
    pretty_echo "Removing Old Versions of Docker"
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
    pretty_echo "Installing Dependencies"
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
    pretty_echo "Adding docker gpg key"
    sudo install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/${ID}/gpg | sudo gpg --yes --dearmor -o /etc/apt/keyrings/docker.gpg
    sudo chmod a+r /etc/apt/keyrings/docker.gpg
    echo "Done"
}

add_to_apt() {
    pretty_echo "Adding docker to apt source"
    echo \
        "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/${ID} \
        $(. /etc/os-release && echo $VERSION_CODENAME) stable" | \
        sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    echo "Done"
}

apt_install_docker() {
    pretty_echo "Installing Docker"
    sudo apt-get update
    sudo apt-get install -y \
        docker-ce \
        docker-ce-cli \
        containerd.io \
        docker-buildx-plugin \
        docker-compose-plugin \
        docker-ce-rootless-extras
}

check_user_not_root() {
    pretty_echo "Use non-root user"

    if [ "$(id -u)" -eq 0 ]; then
        if id "fmtm" &>/dev/null; then
            echo "Current user is root. Switching to existing non-privileged user 'fmtm'."
        else
            echo "Current user is root. Creating a non-privileged user 'fmtm'."
            useradd -m -s /bin/bash fmtm
        fi

        echo "Rerunning this script as user 'fmtm'."
        sudo -u fmtm bash -c "$0 $*"
        exit 0
    fi
}

update_to_rootless() {
    pretty_echo "Disabling docker service if running"
    sudo systemctl disable --now docker.service docker.socket

    pretty_echo "Install rootless docker"
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
    pretty_echo "Allowing Privileged Port Usage"
    sudo tee -a /etc/sysctl.conf <<EOF
net.ipv4.ip_unprivileged_port_start=0
EOF
    sudo sysctl -p
    echo "Done"
}

update_docker_ps_format() {
    pretty_echo "Updating docker ps formatting"
    tee ~/.docker/config.json <<EOF
{
    "psFormat": "table {{.ID}}\\t{{.Image}}\\t{{.Status}}\\t{{.Names}}"
}
EOF
}

add_vars_to_bashrc() {
    heading_echo "Adding rootless DOCKER_HOST to bashrc"

    user_id=$(id -u)
    docker_host_var="export DOCKER_HOST=unix:///run/user/$user_id//docker.sock"
    dc_alias_cmd="alias dc='docker compose'"

    # Check if DOCKER_HOST is already defined
    if ! grep -q "$docker_host_var" ~/.bashrc; then
        echo "Adding rootless DOCKER_HOST var to ~/.bashrc."
        echo "$docker_host_var" >> ~/.bashrc
    fi

    echo "Done"
    echo

    heading_echo "Adding dc='docker compose' alias"

    # Check if the alias already exists
    if ! grep -q "$dc_alias_cmd" ~/.bashrc; then
        echo "Adding 'dc' alias to ~/.bashrc."
        echo "$dc_alias_cmd" >> ~/.bashrc
    fi

    echo "Done"
}

install_docker() {
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
}

check_user_not_root
trap cleanup_and_exit INT
install_docker
