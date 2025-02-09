#!/bin/bash

# Function for section separators
separator() {
    echo "============================================================"
}

highlight() {
    echo -e "\n🔹 $1\n"
}

error_msg() {
    echo -e "\n❌ Error: $1\n"
}

success_msg() {
    echo -e "\n✅ $1\n"
}

# Function to determine if we're running in a Docker container
in_docker() {
    [ -f /.dockerenv ] || grep -Eq '(lxc|docker)' /proc/1/cgroup
}

# Function to handle sudo_cmd based on environment
sudo_cmd() {
    if in_docker; then
        "$@"
    else
        sudo "$@"
    fi
}