#!/bin/bash

# A script to install Docker on Ubuntu with detailed steps and explanations

set -e  # Exit immediately if a command exits with a non-zero status
set -o pipefail  # Exit on pipe errors
# set -x  # Print commands before execution

echo "Starting Docker installation on Ubuntu..."

# Function to determine if we're running in a Docker container
in_docker() {
    [ -f /.dockerenv ] || grep -Eq '(lxc|docker)' /proc/1/cgroup
}

# Function to handle sudo based on environment
sudo_cmd() {
    if in_docker; then
        "$@"
    else
        sudo "$@"
    fi
}

# Update system
sudo_cmd apt-get update -y

# Install prerequisites
sudo_cmd apt-get install -y ca-certificates curl

# Set up Docker repository
sudo_cmd install -m 0755 -d /etc/apt/keyrings
sudo_cmd curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo_cmd chmod a+r /etc/apt/keyrings/docker.asc

# Add Docker repository
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo_cmd tee /etc/apt/sources.list.d/docker.list > /dev/null

# Update and install Docker
sudo_cmd apt-get update -y
sudo_cmd apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Set up permissions
if getent group docker > /dev/null 2>&1; then
    echo "Docker group exists"
else
    sudo_cmd groupadd docker
fi

sudo_cmd usermod -aG docker $USER

# Restart Docker daemon
sudo_cmd systemctl enable docker
sudo_cmd systemctl restart docker
echo
echo
echo "==============================================="
echo "Docker installation completed!"
echo "To complete setup, choose ONE of these options:"
echo "1. Log out and log back in to Ubuntu"
echo "2. Run this command in a new terminal:"
echo "   exec su -l $USER"
echo "==============================================="

# Don't run verification commands here - they'll fail until user session is refreshed