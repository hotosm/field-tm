#!/bin/bash

# Tested for Ubuntu 22.04 LTS & Debian 11 Bookworm

# TODO docker-compose is required, install equivalent for podman and alias

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

check_os() {
    pretty_echo "Checking Current OS"

    if [ -e /etc/os-release ]; then
        source /etc/os-release
        case "$ID" in
        debian)
            echo "Current OS is ${PRETTY_NAME}."
            ;;
        ubuntu)
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

install_podman() {
    pretty_echo "Installing Podman"
    sudo apt-get update
    sudo apt-get install -y \
        podman
}

allow_priv_port_usage() {
    pretty_echo "Allowing privileged port usage"
    sudo tee -a /etc/sysctl.conf <<EOF
net.ipv4.ip_unprivileged_port_start=0
EOF
    sudo sysctl -p
    echo "Done"
}

create_docker_alias() {
    pretty_echo "Adding docker='podman' alias"
    echo "alias docker='podman'" >> ~/.bashrc
    echo "Done"
}


# Podman install process
check_os
install_podman
allow_priv_port_usage
create_docker_alias
