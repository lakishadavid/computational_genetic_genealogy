#!/bin/bash

# A script to install Docker on Ubuntu with detailed steps and explanations

set -e  # Exit immediately if a command exits with a non-zero status
set -o pipefail  # Exit on pipe errors

echo "Starting Docker installation on Ubuntu..."

# Step 1: Update the package lists
echo "Updating package lists..."
sudo apt-get update -y

# Step 2: Install prerequisite packages
# `ca-certificates`: Ensure HTTPS support
# `curl`: Command-line tool for downloading files
echo "Installing prerequisite packages (ca-certificates and curl)..."
sudo apt-get install -y ca-certificates curl

# Step 3: Create a directory for Docker's GPG key
echo "Creating directory for Docker's GPG key..."
sudo install -m 0755 -d /etc/apt/keyrings

# Step 4: Download Docker's official GPG key
echo "Downloading Docker's official GPG key..."
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc

# Step 5: Set permissions for the GPG key
echo "Setting permissions for Docker's GPG key..."
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Step 6: Add Docker's repository to the system's Apt sources
# Replace placeholders with architecture and Ubuntu version
echo "Adding Docker's repository to Apt sources..."
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Step 7: Update package lists to include Docker's repository
echo "Updating package lists to include Docker's repository..."
sudo apt-get update -y

# Step 8: Install Docker packages
# `docker-ce`: Docker Community Edition
# `docker-ce-cli`: Command-line interface for Docker
# `containerd.io`: Container runtime for Docker
# `docker-buildx-plugin`: BuildKit plugin for Docker
# `docker-compose-plugin`: Docker Compose plugin
echo "Installing Docker packages..."
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Step 9: Test Docker installation
# The `hello-world` image verifies the Docker installation is successful.
echo "Verifying Docker installation with a test image..."
sudo docker run hello-world

echo "Docker installation completed successfully!"