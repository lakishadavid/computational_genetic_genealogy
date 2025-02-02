#!/bin/bash

CONTAINER_NAME="cgg_container"

# Check if the container is running
if [ "$(docker ps -q -f name=$CONTAINER_NAME)" == "" ]; then
    echo "Container is not running. Starting now..."
    docker start $CONTAINER_NAME
fi

# Transfer files **INTO** the container
if [[ "$1" == "in" ]]; then
    echo "Copying files into the container..."
    docker cp "$(pwd)/data" $CONTAINER_NAME:/home/ubuntu/
    docker cp "$(pwd)/results" $CONTAINER_NAME:/home/ubuntu/
    docker cp "$(pwd)/references" $CONTAINER_NAME:/home/ubuntu/
    echo "Files copied into the container."

# Transfer files **OUT** of the container
elif [[ "$1" == "out" ]]; then
    echo "Copying files from the container to local machine..."
    docker cp $CONTAINER_NAME:/home/ubuntu/data ./data
    docker cp $CONTAINER_NAME:/home/ubuntu/results ./results
    docker cp $CONTAINER_NAME:/home/ubuntu/references ./references
    echo "Files copied from the container."

else
    echo "Usage: bash transfer_files.sh [in|out]"
    echo " - in  → Copies local files into the container"
    echo " - out → Copies files from the container to the local machine"
fi