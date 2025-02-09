#!/bin/bash

set -e  # Exit on error
set -o pipefail  # Exit on pipe errors

# Function for messages
highlight() {
    echo -e "\n🔹 $1\n"
}

error_msg() {
    echo -e "\n❌ Error: $1\n"
    exit 1
}

# Clean up any existing container with the same name
highlight "Cleaning up any existing test container..."
docker rm -f test-ubuntu 2>/dev/null || true

# Pull the Ubuntu 22.04 image
highlight "Pulling Ubuntu 22.04 image..."
docker pull ubuntu:22.04 || error_msg "Failed to pull Ubuntu image"

# Start a persistent container in detached mode
highlight "Starting test container..."
docker run -dit --name test-ubuntu ubuntu:22.04 || error_msg "Failed to start container"

# Install required packages inside the running container
highlight "Installing basic requirements..."
docker exec test-ubuntu apt update && \
docker exec test-ubuntu apt install -y sudo git locales || error_msg "Failed to install basic packages"

# Set system locale
highlight "Configuring locale..."
docker exec test-ubuntu locale-gen en_US.UTF-8 && \
docker exec test-ubuntu update-locale LANG=en_US.UTF-8 && \
docker exec test-ubuntu bash -c "export LANG=en_US.UTF-8" || error_msg "Failed to set locale"

# Create a non-root user (blankuser)
highlight "Creating test user..."
docker exec test-ubuntu adduser --disabled-password --gecos "" blankuser && \
docker exec test-ubuntu usermod -aG sudo blankuser || error_msg "Failed to create user"

# Grant blankuser passwordless sudo
highlight "Configuring sudo access..."
docker exec test-ubuntu bash -c "echo 'blankuser ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/blankuser" && \
docker exec test-ubuntu chmod 0440 /etc/sudoers.d/blankuser || error_msg "Failed to configure sudo"

# Configure Git as blankuser
highlight "Configuring Git..."
docker exec -it test-ubuntu su - blankuser -c "git config --global user.name 'LaKisha David'" && \
docker exec -it test-ubuntu su - blankuser -c "git config --global user.email 'lakishatdavid@gmail.com'" || error_msg "Failed to configure Git"

# Clone the repository as blankuser
highlight "Cloning repository..."
docker exec -it test-ubuntu su - blankuser -c "git clone https://github.com/lakishadavid/computational_genetic_genealogy.git" || error_msg "Failed to clone repository"

# Success message with instructions
separator() {
    echo "============================================================"
}

separator
highlight "Test environment ready!"
separator
echo "
To test the setup script:
1. You will now be dropped into the test environment
2. Navigate to the project directory:
   cd computational_genetic_genealogy
3. Run the setup script WITH SUDO:
   sudo bash scripts_env/setup_env.sh

NOTE: The setup needs sudo privileges for system packages installation.
      Don't worry - you're already configured for passwordless sudo.

To clean up when done:
1. Exit the container (type 'exit' or Ctrl+D)
2. Run: docker rm -f test-ubuntu
"
separator

# Drop into the test environment
highlight "Switching to test environment..."
docker exec -it test-ubuntu su - blankuser