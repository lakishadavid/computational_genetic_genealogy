#!/bin/bash

# This script creates a Docker container to test manual installation instructions
# in a clean Ubuntu 24.04 environment.
#
# Usage: bash test_manual_install.sh [container_name] [host_volume_dir]
# Defaults:
#   container_name: ubuntu_test_env
#   host_volume_dir: ~/test_volume (for persistence between tests)
#
# Example: bash test_manual_install.sh
# Example with custom name: bash test_manual_install.sh my_test_container ~/my_test_volume
#
# Notes:
# - This will create a persistent volume to save your progress between sessions
# - The container runs interactively, giving you a bash shell to work with
# - The repository isn't auto-cloned, so you'll test the full process starting from git clone

# Assign variables with defaults if not provided
CONTAINER_NAME="${1:-ubuntu_test_env}"
HOST_VOLUME_DIR="${2:-${HOME}/test_volume}"

# Exit immediately if a command exits with a non-zero status
set -e

# Create log directory
LOG_DIR="./logs"
mkdir -p "${LOG_DIR}"

# Create a timestamped log file
LOG_FILE="${LOG_DIR}/test_manual_install_$(date +%Y%m%d_%H%M%S).log"
touch "${LOG_FILE}"
echo "Test environment setup started at: $(date)" | tee -a "${LOG_FILE}"

# Create a Docker volume for persistence if it doesn't exist
echo "Step 1: Creating Docker volume directory (if it doesn't exist)..." | tee -a "${LOG_FILE}"
mkdir -p "${HOST_VOLUME_DIR}"

# Stop and remove the test container if it exists
echo "Step 2: Checking for existing test container..." | tee -a "${LOG_FILE}"
if docker ps -a | grep -q "${CONTAINER_NAME}"; then
    echo "Found existing container. Stopping and removing it..." | tee -a "${LOG_FILE}"
    docker stop "${CONTAINER_NAME}" 2>&1 | tee -a "${LOG_FILE}"
    docker rm "${CONTAINER_NAME}" 2>&1 | tee -a "${LOG_FILE}"
fi

# Pull the latest Ubuntu 24.04 image
echo "Step 3: Pulling latest Ubuntu 24.04 image..." | tee -a "${LOG_FILE}"
docker pull ubuntu:24.04 2>&1 | tee -a "${LOG_FILE}"

# Create and run the container with X11 forwarding for GUI apps (optional)
echo "Step 4: Creating and starting test container..." | tee -a "${LOG_FILE}"
docker run -it -d \
    --name "${CONTAINER_NAME}" \
    -v "${HOST_VOLUME_DIR}:/home/testuser" \
    -v /tmp/.X11-unix:/tmp/.X11-unix \
    -e DISPLAY="${DISPLAY}" \
    -e TERM=xterm-256color \
    --workdir /home/testuser \
    ubuntu:24.04 \
    /bin/bash 2>&1 | tee -a "${LOG_FILE}"

# Install basic utilities and create a test user
echo "Step 5: Installing basic utilities and setting up test user..." | tee -a "${LOG_FILE}"
docker exec -i "${CONTAINER_NAME}" bash -c "
    apt-get update && \
    apt-get install -y sudo git wget curl nano python3 htop procps xauth openssh-client \
                       x11-apps iputils-ping net-tools && \
    useradd -m testuser -s /bin/bash && \
    echo 'testuser ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/testuser && \
    chmod 0440 /etc/sudoers.d/testuser && \
    chown -R testuser:testuser /home/testuser
" 2>&1 | tee -a "${LOG_FILE}"

# Print instructions for accessing the container
echo -e "\n\n========== INSTRUCTIONS ==========\n" | tee -a "${LOG_FILE}"
echo "Container '${CONTAINER_NAME}' is now running with a fresh Ubuntu 24.04 installation." | tee -a "${LOG_FILE}"
echo "" | tee -a "${LOG_FILE}"
echo "To access the container and test your instructions:" | tee -a "${LOG_FILE}"
echo "1. Connect to the container as root:" | tee -a "${LOG_FILE}"
echo "   docker exec -it ${CONTAINER_NAME} bash" | tee -a "${LOG_FILE}"
echo "" | tee -a "${LOG_FILE}"
echo "2. Then switch to the test user:" | tee -a "${LOG_FILE}"
echo "   su - testuser" | tee -a "${LOG_FILE}"
echo "" | tee -a "${LOG_FILE}"
echo "3. Now follow your README instructions, starting with:" | tee -a "${LOG_FILE}"
echo "   git clone https://github.com/lakishadavid/computational_genetic_genealogy.git" | tee -a "${LOG_FILE}"
echo "" | tee -a "${LOG_FILE}" 
echo "4. When finished testing, exit the container but keep it running:" | tee -a "${LOG_FILE}"
echo "   type 'exit' (twice if you're in the testuser shell)" | tee -a "${LOG_FILE}"
echo "" | tee -a "${LOG_FILE}"
echo "5. To stop the container when you're done:" | tee -a "${LOG_FILE}"
echo "   docker stop ${CONTAINER_NAME}" | tee -a "${LOG_FILE}"
echo "" | tee -a "${LOG_FILE}"
echo "6. To restart and reconnect later:" | tee -a "${LOG_FILE}"
echo "   docker start ${CONTAINER_NAME}" | tee -a "${LOG_FILE}"
echo "   docker exec -it ${CONTAINER_NAME} bash" | tee -a "${LOG_FILE}"
echo "" | tee -a "${LOG_FILE}"
echo "Your changes will be preserved in: ${HOST_VOLUME_DIR}" | tee -a "${LOG_FILE}"
echo "" | tee -a "${LOG_FILE}"
echo "To test VS Code integration with the container, install the VS Code" | tee -a "${LOG_FILE}"
echo "'Remote - Containers' extension and use 'Attach to Running Container...'" | tee -a "${LOG_FILE}"
echo "to connect to ${CONTAINER_NAME}" | tee -a "${LOG_FILE}"
echo "" | tee -a "${LOG_FILE}"
echo "Log file available at: ${LOG_FILE}" | tee -a "${LOG_FILE}"