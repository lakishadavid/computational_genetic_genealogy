#!/bin/bash

# A script to install Docker on Ubuntu with detailed steps and explanations

set -e  # Exit immediately if a command exits with a non-zero status
set -o pipefail  # Exit on pipe errors
# set -x  # Print commands before execution

echo "Starting Docker installation on Ubuntu..."

# Update system
sudo apt-get update -y

# Install prerequisites
sudo apt-get install -y ca-certificates curl

# Set up Docker repository
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add Docker repository
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Update and install Docker
sudo apt-get update -y
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Set up permissions
if getent group docker > /dev/null 2>&1; then
    echo "Docker group exists"
else
    sudo groupadd docker
fi

sudo usermod -aG docker $USER

# Restart Docker daemon
sudo systemctl enable docker
sudo systemctl restart docker
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