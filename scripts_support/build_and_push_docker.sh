#!/bin/bash

# This script builds a Docker image, optionally pushes it to Docker Hub,
# and provides options to enter the container or delete the container and image.
#
# Before running this script, ensure you are logged in:
#   docker login
#
# Usage: bash scripts_env/build_and_push_docker.sh [docker_username] [image_name] [image_tag] [dockerfile_dir] [action]
# Defaults:
#   docker_username: lakishadavid
#   image_name: cgg_image
#   image_tag: latest
#   dockerfile_dir: .
#   action: build (options: build, build_push, enter, delete)
#
# Examples:
#   bash scripts_env/build_and_push_docker.sh                         # Build only
#   bash scripts_env/build_and_push_docker.sh lakishadavid cgg_image latest . build_push  # Build and push
#   bash scripts_env/build_and_push_docker.sh lakishadavid cgg_image latest . enter       # Build and enter container
#   bash scripts_env/build_and_push_docker.sh lakishadavid cgg_image latest . delete      # Delete container and image

# Assign variables with defaults if not provided
DOCKER_USERNAME="${1:-lakishadavid}"
IMAGE_NAME="${2:-cgg_image}"
IMAGE_TAG="${3:-latest}"
DOCKERFILE_DIR="${4:-.}"
ACTION="${5:-build}"  # Default action is build only

# Full image name
FULL_IMAGE_NAME="${DOCKER_USERNAME}/${IMAGE_NAME}:${IMAGE_TAG}"

# Exit immediately if a command exits with a non-zero status
set -e

# Create a timestamped log file
LOG_FILE="/home/lakishadavid/computational_genetic_genealogy/logs/docker_operations.log"
mkdir -p "$(dirname "${LOG_FILE}")" 2>/dev/null || true
touch "${LOG_FILE}"
echo "Operation started at: $(date)" | tee -a "${LOG_FILE}"

# Function to check if a container with the image exists
container_exists() {
    CONTAINER_ID=$(docker ps -a --filter "ancestor=${FULL_IMAGE_NAME}" --format "{{.ID}}")
    if [ -n "${CONTAINER_ID}" ]; then
        return 0  # Container exists
    else
        return 1  # Container does not exist
    fi
}

# Function to build the Docker image
build_image() {
    echo "Step 1: Stopping and removing containers based on ${IMAGE_NAME}..." | tee -a "${LOG_FILE}"
    docker ps -a | grep ${IMAGE_NAME} | awk '{print $1}' | xargs -r docker rm -f 2>&1 | tee -a "${LOG_FILE}" || true

    echo "Step 2: Removing existing image (if it exists)..." | tee -a "${LOG_FILE}"
    if docker image inspect "${FULL_IMAGE_NAME}" >/dev/null 2>&1; then
        docker rmi -f "${FULL_IMAGE_NAME}" 2>&1 | tee -a "${LOG_FILE}" || true
    fi

    echo "Step 3: Building Docker image..." | tee -a "${LOG_FILE}"
    docker build --no-cache -t "${FULL_IMAGE_NAME}" "${DOCKERFILE_DIR}" 2>&1 | tee -a "${LOG_FILE}"
    echo "Image built successfully: ${FULL_IMAGE_NAME}" | tee -a "${LOG_FILE}"
}

# Function to push the Docker image to Docker Hub
push_image() {
    echo "Pushing Docker image to Docker Hub..." | tee -a "${LOG_FILE}"
    docker push "${FULL_IMAGE_NAME}" 2>&1 | tee -a "${LOG_FILE}"
    echo "Image pushed successfully: ${FULL_IMAGE_NAME}" | tee -a "${LOG_FILE}"
}

# Function to enter an existing container or create and enter a new one
enter_container() {
    if container_exists; then
        CONTAINER_ID=$(docker ps -a --filter "ancestor=${FULL_IMAGE_NAME}" --format "{{.ID}}" | head -n 1)
        echo "Entering existing container: ${CONTAINER_ID}..." | tee -a "${LOG_FILE}"
        docker start -ai "${CONTAINER_ID}" 2>&1 | tee -a "${LOG_FILE}"
    else
        echo "Creating and entering new container from image: ${FULL_IMAGE_NAME}..." | tee -a "${LOG_FILE}"
        docker run -it "${FULL_IMAGE_NAME}" bash 2>&1 | tee -a "${LOG_FILE}"
    fi
}

# Function to delete containers and image
delete_resources() {
    echo "Stopping and removing all containers based on ${FULL_IMAGE_NAME}..." | tee -a "${LOG_FILE}"
    CONTAINER_IDS=$(docker ps -a --filter "ancestor=${FULL_IMAGE_NAME}" --format "{{.ID}}")
    if [ -n "${CONTAINER_IDS}" ]; then
        echo "${CONTAINER_IDS}" | xargs docker rm -f 2>&1 | tee -a "${LOG_FILE}"
        echo "Containers removed successfully." | tee -a "${LOG_FILE}"
    else
        echo "No containers found for ${FULL_IMAGE_NAME}." | tee -a "${LOG_FILE}"
    fi

    echo "Removing image: ${FULL_IMAGE_NAME}..." | tee -a "${LOG_FILE}"
    if docker image inspect "${FULL_IMAGE_NAME}" >/dev/null 2>&1; then
        docker rmi -f "${FULL_IMAGE_NAME}" 2>&1 | tee -a "${LOG_FILE}"
        echo "Image removed successfully." | tee -a "${LOG_FILE}"
    else
        echo "Image ${FULL_IMAGE_NAME} not found." | tee -a "${LOG_FILE}"
    fi
}

# Main execution based on the action
case "${ACTION}" in
    build)
        build_image
        echo "Complete: Docker image successfully built." | tee -a "${LOG_FILE}"
        ;;
    build_push)
        build_image
        push_image
        echo "Complete: Docker image successfully built and pushed." | tee -a "${LOG_FILE}"
        ;;
    enter)
        # If image doesn't exist, build it first
        if ! docker image inspect "${FULL_IMAGE_NAME}" >/dev/null 2>&1; then
            echo "Image not found. Building first..." | tee -a "${LOG_FILE}"
            build_image
        fi
        enter_container
        ;;
    delete)
        delete_resources
        echo "Complete: Containers and image deleted." | tee -a "${LOG_FILE}"
        ;;
    *)
        echo "Invalid action: ${ACTION}" | tee -a "${LOG_FILE}"
        echo "Valid actions are: build, build_push, enter, delete" | tee -a "${LOG_FILE}"
        exit 1
        ;;
esac

echo "Log file available at: ${LOG_FILE}" | tee -a "${LOG_FILE}"