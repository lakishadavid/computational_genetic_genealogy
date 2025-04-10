#!/bin/bash
# Script to clean Docker environment and rebuild fresh Ubuntu 22.04 container

echo "====================================================="
echo "Docker Environment Cleanup and Fresh Install"
echo "====================================================="

# Define the correct path to the installation script
INSTALL_SCRIPT_PATH="/home/lakishadavid/computational_genetic_genealogy/scripts_support/install_ubuntu22_docker.sh"

# Verify install script exists
if [ ! -f "$INSTALL_SCRIPT_PATH" ]; then
    echo "❌ Error: Installation script not found at: $INSTALL_SCRIPT_PATH"
    echo "Please check the path to the installation script."
    exit 1
fi

# Stop all running containers
echo "Stopping all running containers..."
docker stop $(docker ps -q) 2>/dev/null || echo "No running containers to stop."

# List all containers related to Ubuntu 22.04
echo -e "\nListing Ubuntu 22.04 related containers:"
docker ps -a | grep ubuntu:22.04

# Prompt for confirmation before removing containers
read -p "Would you like to remove all Ubuntu 22.04 containers? (y/n): " confirm
if [[ $confirm == [yY] || $confirm == [yY][eE][sS] ]]; then
    # Remove all Ubuntu 22.04 related containers
    container_ids=$(docker ps -a | grep ubuntu:22.04 | awk '{print $1}')
    if [ ! -z "$container_ids" ]; then
        echo "Removing Ubuntu 22.04 containers..."
        docker rm $container_ids
        echo "✅ Containers removed."
    else
        echo "No Ubuntu 22.04 containers found to remove."
    fi
else
    echo "Skipping container removal."
fi

# Clean unused Docker resources
echo -e "\nCleaning unused Docker resources (volumes, networks, etc.)..."
docker system prune -f
echo "✅ Docker system pruned."

# Pull fresh Ubuntu 22.04 image
echo -e "\nPulling fresh Ubuntu 22.04 image..."
docker pull ubuntu:22.04
echo "✅ Fresh Ubuntu 22.04 image pulled."

# Create a new container with port forwarding for Jupyter
echo -e "\nCreating a new Ubuntu 22.04 container with Jupyter port forwarding..."
docker run -it -d --name cgg_fresh_env -p 8888:8888 ubuntu:22.04
container_id=$(docker ps -a | grep cgg_fresh_env | awk '{print $1}')

# Copy installation script to the container
echo -e "\nCopying installation script to the container..."
docker cp "$INSTALL_SCRIPT_PATH" cgg_fresh_env:/install_ubuntu22_docker.sh
docker exec -it cgg_fresh_env chmod +x /install_ubuntu22_docker.sh
echo "✅ Installation script copied and made executable."

# Ask if user wants to attach to container
read -p "Would you like to attach to the container now? (y/n): " attach
if [[ $attach == [yY] || $attach == [yY][eE][sS] ]]; then
    echo -e "\n====================================================="
    echo "Attaching to container..."
    echo "To run the installation script, type: /install_ubuntu22_docker.sh"
    echo "====================================================="
    sleep 2
    docker exec -it cgg_fresh_env bash
else
    echo -e "\n====================================================="
    echo "Setup Complete!"
    echo "====================================================="
    echo "Container ID: $container_id"
    echo "Container Name: cgg_fresh_env"
    echo -e "\nTo attach to your new container:"
    echo "  docker exec -it cgg_fresh_env bash"
    echo -e "\nThe installation script is already copied to the container at:"
    echo "  /install_ubuntu22_docker.sh"
    echo -e "\nTo run the installation script inside the container:"
    echo "  1. Attach to the container: docker exec -it cgg_fresh_env bash"
    echo "  2. Run the script: /install_ubuntu22_docker.sh"
    echo -e "\nTo stop the container when finished:"
    echo "  docker stop cgg_fresh_env"
    echo "====================================================="
fi