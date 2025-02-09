#!/bin/bash

# Pull the Ubuntu 22.04 image
docker pull ubuntu:22.04

# Start a persistent container in detached mode
docker run -dit --name test-ubuntu ubuntu:22.04

# Install required packages inside the running container
docker exec test-ubuntu apt update && docker exec test-ubuntu apt install -y sudo git locales

# Set system locale
docker exec test-ubuntu locale-gen en_US.UTF-8
docker exec test-ubuntu update-locale LANG=en_US.UTF-8
docker exec test-ubuntu bash -c "export LANG=en_US.UTF-8"

# Create a non-root user (blankuser)
docker exec test-ubuntu adduser --disabled-password --gecos "" blankuser
docker exec test-ubuntu usermod -aG sudo blankuser

# Grant blankuser passwordless sudo
docker exec test-ubuntu bash -c "echo 'blankuser ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/blankuser"
docker exec test-ubuntu chmod 0440 /etc/sudoers.d/blankuser

# Configure Git as blankuser
docker exec -it test-ubuntu su - blankuser -c "git config --global user.name 'LaKisha David'"
docker exec -it test-ubuntu su - blankuser -c "git config --global user.email 'lakishatdavid@gmail.com'"

# Clone the repository as blankuser
docker exec -it test-ubuntu su - blankuser -c "git clone https://github.com/lakishadavid/computational_genetic_genealogy.git"

# Run the setup script inside the repository
docker exec -it test-ubuntu su - blankuser -c "cd computational_genetic_genealogy && sudo bash scripts_env/setup_env.sh"

# Switch to blankuser interactively (keeps the session open)
docker exec -it test-ubuntu su - blankuser

# docker rm -f test-ubuntu