#!/bin/bash

# This script builds a Docker image and optionally pushes it to Docker Hub.
# Before running this script, ensure you are logged in:
#   docker login
#
# Usage: bash scripts_env/build_and_push_docker.sh [docker_username] [image_name] [image_tag] [dockerfile_dir] [build_only]
# Defaults:
#   docker_username: lakishadavid
#   image_name: cgg_image
#   image_tag: latest
#   dockerfile_dir: .
#   build_only: false
#
# Example: bash scripts_env/build_and_push_docker.sh
# Example (build only): bash scripts_env/build_and_push_docker.sh lakishadavid cgg_image latest . true
# Example (push built image): docker push lakishadavid/cgg_image:latest
# Example (run built image): docker run -it lakishadavid/cgg_image:latest bash
# To rerun the container with the same state: docker start -ai <container_id>
# docker rm -f $(docker ps -a -q)
# docker rmi -f $(docker images -q)



# Assign variables with defaults if not provided
DOCKER_USERNAME="${1:-lakishadavid}"
IMAGE_NAME="${2:-cgg_image}"
IMAGE_TAG="${3:-latest}"
DOCKERFILE_DIR="${4:-.}"
BUILD_ONLY="${5:-false}"

# Exit immediately if a command exits with a non-zero status
set -e

# Create a timestamped log file
LOG_FILE="/home/lakishadavid/computational_genetic_genealogy/build.log"
rm -f "${LOG_FILE}"  # Delete existing log file
touch "${LOG_FILE}"
echo "Build started at: $(date)" | tee -a "${LOG_FILE}"

# Stop and remove all containers using the image
echo "Step 1: Stopping and removing containers..." | tee "${LOG_FILE}"
docker ps -a | grep ${IMAGE_NAME} | awk '{print $1}' | xargs -r docker rm -f 2>&1 | tee -a "${LOG_FILE}"

# Remove the existing image if it exists
echo "Step 2: Removing existing image (if it exists)..." | tee -a "${LOG_FILE}"
if docker image inspect "${DOCKER_USERNAME}/${IMAGE_NAME}:${IMAGE_TAG}" >/dev/null 2>&1; then
    docker rmi -f "${DOCKER_USERNAME}/${IMAGE_NAME}:${IMAGE_TAG}" 2>&1 | tee -a "${LOG_FILE}"
fi

# Build the Docker image
echo "Step 3: Building Docker image..." | tee -a "${LOG_FILE}"
docker build -t "${DOCKER_USERNAME}/${IMAGE_NAME}:${IMAGE_TAG}" "${DOCKERFILE_DIR}" 2>&1 | tee -a "${LOG_FILE}"

# Push the Docker image to Docker Hub if build_only is false
if [ "${BUILD_ONLY}" != "true" ]; then
    echo "Step 4: Pushing Docker image..." | tee -a "${LOG_FILE}"
    docker push "${DOCKER_USERNAME}/${IMAGE_NAME}:${IMAGE_TAG}" 2>&1 | tee -a "${LOG_FILE}"
    echo "Complete: Docker image successfully built and pushed." | tee -a "${LOG_FILE}"
else
    echo "Complete: Docker image successfully built. Skipping push as requested." | tee -a "${LOG_FILE}"
fi

echo "Log file available at: ${LOG_FILE}" | tee -a "${LOG_FILE}"