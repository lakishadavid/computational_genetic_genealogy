#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Set the image name
IMAGE_NAME="bagg_analysis"

# Check if the Docker image already exists
if [[ "$(docker images -q $IMAGE_NAME 2> /dev/null)" == "" ]]; then
  echo "Docker image '$IMAGE_NAME' not found. Building the image..."
  docker build -t $IMAGE_NAME .
else
  echo "Docker image '$IMAGE_NAME' already exists."
fi

# Run the container
echo "Running the Docker container..."
docker run -it --rm $IMAGE_NAME


Here’s a Docker Instruction Guide tailored for your students, focusing on running pre-built Docker images that you provide. This guide includes both basic instructions and a helper script for mapping local directories using Docker volumes.
https://docs.docker.com/get-started/
https://hub.docker.com/

Docker Instruction Guide for Students
1. Install Docker
On Linux (e.g., Ubuntu):

Update the package index:
bash
Copy code
sudo apt-get update
Install Docker:
bash
Copy code
sudo apt-get install -y docker.io
Start and enable Docker:
bash
Copy code
sudo systemctl start docker
sudo systemctl enable docker
Add your user to the Docker group (optional but recommended):
bash
Copy code
sudo usermod -aG docker $USER
Log out and log back in to apply this change.
On Windows/Mac:

Download and install Docker Desktop from Docker’s official website.
Follow the installation prompts, ensuring WSL2 integration is enabled if on Windows.
Verify Installation: Run this command in a terminal:

bash
Copy code
docker run hello-world
If Docker is installed correctly, you will see the "Hello from Docker!" message.
2. Running a Docker Image
Receive the Docker Image:

Your instructor will provide the Docker image as a .tar file (e.g., my-container.tar) or via a container registry like Docker Hub.
Load the Docker Image (if provided as a .tar file):

bash
Copy code
docker load < my-container.tar
This makes the image available locally.
Run the Docker Image: Use the docker run command to start a container from the image:

bash
Copy code
docker run my-container
Replace my-container with the name of the image.
3. Mapping Local Directories
If the container needs to access your local directories (e.g., results, data), you’ll need to map them into the container using Docker volumes.

Using the Command Line: To run the container and map your local directories, use the -v option:

bash
Copy code
# docker run --rm -v /path/to/data:/data -v /path/to/results:/results myimage
# docker run --rm -v /path/to/data:/data -v /path/to/results:/results --user $(id -u):$(id -g) myimage
# docker run --rm \
#   --mount type=bind,source=/path/to/data,target=/data \
#   --mount type=bind,source=/path/to/results,target=/results \
#   --user $(id -u):$(id -g) \
#   myimage

docker run -v /path/to/local/results:/results_directory \
           -v /path/to/local/references:/references_directory \
           my-container
Replace /path/to/local/results and /path/to/local/references with the actual paths on your machine.
The container will access these directories as /results_directory and /references_directory.
Using a Helper Script: To simplify this process, use the provided run_container.sh script (see below).

4. Common Docker Commands
Here are some basic Docker commands you might find helpful:

List all Docker images on your system:
bash
Copy code
docker images
List all running containers:
bash
Copy code
docker ps
Stop a running container:
bash
Copy code
docker stop <container-id>
Remove a container (after stopping it):
bash
Copy code
docker rm <container-id>
Remove an image:
bash
Copy code
docker rmi <image-id>
Helper Script for Running Containers
Save the following script as run_container.sh and provide it to your students. This script simplifies the process of mapping local directories and running the container.

Script: run_container.sh
bash
Copy code
#!/bin/bash

# Default local directories if none are provided
RESULTS_DIR=${1:-$PWD/results}
REFERENCES_DIR=${2:-$PWD/references}

# Check if the directories exist
if [ ! -d "$RESULTS_DIR" ]; then
    echo "Error: Results directory ($RESULTS_DIR) does not exist."
    exit 1
fi

if [ ! -d "$REFERENCES_DIR" ]; then
    echo "Error: References directory ($REFERENCES_DIR) does not exist."
    exit 1
fi

# Run the container with volume mappings
docker run -v "$RESULTS_DIR:/results_directory" \
           -v "$REFERENCES_DIR:/references_directory" \
           my-container
How Students Use the Script
Save the script as run_container.sh.
Make it executable:
bash
Copy code
chmod +x run_container.sh
Run the script, specifying their local directories:
bash
Copy code
./run_container.sh /path/to/results /path/to/references
If no directories are provided, it defaults to ./results and ./references in the current directory.
What You Provide to Students
The Docker Image:

Share the .tar file or the Docker Hub repository link.
The Helper Script:

Provide run_container.sh for ease of use.
This Instruction Guide:

Ensure students have a copy of this guide for installation and usage instructions.
Summary
Students install Docker and verify it with hello-world.
They load and run your pre-built Docker images.
Local directories are mapped into the container using either the -v option or the run_container.sh script.
Provide all necessary resources: image file, helper script, and instructions.