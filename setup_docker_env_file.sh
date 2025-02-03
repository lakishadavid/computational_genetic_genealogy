#!/bin/bash

if [ ! -f .env ]; then
    echo "Creating .env file with default values..."
    echo "PROJECT_DATA_DIR=/home/ubuntu/data" > .env
    echo "PROJECT_RESULTS_DIR=/home/ubuntu/results" >> .env
    echo "PROJECT_REFERENCES_DIR=/home/ubuntu/references" >> .env
fi

# Keep container running
exec bash
