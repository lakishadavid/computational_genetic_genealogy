**in the terminal**
cd ~/computational_genetic_genealogy

# Run setup
python -m scripts_support.directory_setup

**Build the Docker image**
<!-- docker build -t devcontainer-image . -->
docker compose build

**Open a second terminal window**
docker image ls
# docker image rm [IMAGE_ID or IMAGE_NAME:TAG]
# docker inspect devcontainer-image # metadata
# docker save -o devcontainer-image.tar devcontainer-image # to/from a usb drive or other storage mechanism
# docker load -i devcontainer-image.tar


**Option 1**:
docker run -it --rm devcontainer-image

**Option 2**:
# Run the Docker container with volume mounts
<!-- docker run -it --rm \
    -v /path/to/local/data:/data \
    -v /path/to/local/results:/results \
    -v /path/to/local/references:/references \
    devcontainer-image -->

**Option 3**
<!-- docker-compose up -->

# Run it first time to set up directories
docker compose run --rm app poetry run python -m scripts_support.directory_setup

# After directories are configured, run the container
docker compose up

# For subsequent runs, users just need:
<!-- docker compose up -->


1. **Work on Your Project**:
   - You can now interact with your repository just as you would in a local setup. When reopening the folder in the future, VSCode will automatically use the existing dev container configuration.

---

run scripts...scripts_support.directory_setup for .env file...
poetry run python -m scripts_support.directory_setup

---

When you use docker save:
It saves the base image (everything in your Dockerfile)
It DOES NOT save:
Any files you created while using the container
Any changes you made to the container after it started
Any data in volumes (whether they're mapped to your local machine or container-only)

# get container name or id
docker ps

# Syntax: docker cp <container_id>:/path/in/container /path/on/local/machine
docker cp my_container:/home/ubuntu/results/analysis.csv /path/to/usb/drive/

# Copy entire results directory
docker cp my_container:/home/ubuntu/results/ /path/to/usb/drive/

# Copy file (or directory) from local machine to container
docker cp /path/from/local/machine my_container:/path/in/container

# Save to USB drive (example for Linux/Mac)
docker save -o /media/usb/devcontainer-image.tar devcontainer-image

# Save to USB drive (example for Windows)
docker save -o E:\devcontainer-image.tar devcontainer-image

# Save to Downloads folder
docker save -o ~/Downloads/devcontainer-image.tar devcontainer-image

# Save to current directory
docker save -o ./devcontainer-image.tar devcontainer-image

# To load an image from tar
docker load -i devcontainer-image.tar

---
 https://code.visualstudio.com/docs/devcontainers/containers#_quick-start-open-an-existing-folder-in-a-container


Rebuild with docker-compose.yml
Use the "Rebuild and Reopen in Container..." command and select the docker-compose.yml file.
VSCode will rebuild the container using docker-compose.yml and mount the directories specified in the .env file.

# Print environment variables for debugging (optional)
echo "Starting container with WORKSPACE_DIR=$WORKSPACE_DIR"

echo "Running directory setup..."
poetry run python -m scripts_support.directory_setup

echo "Running installs..."
poetry run python -m scripts_env.run_installs

By default, Docker Compose automatically looks for an .env file in the same directory as the docker-compose.yml file.

docker-compose config

From now on, when you open the project folder, VS Code will automatically pick up and reuse your dev container configuration.
---

check that the volumes are mounted
ls /data
ls /results
ls /references




docker build -t myimage .
docker run -v OR docker-compose.yml


  
entrypoint.sh